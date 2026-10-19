"""Audit the existing resource scenarios against published Seoul benchmarks.

shortcut: historical average costs and unquoted scenario inputs are not matched
incremental costs; replace with local quotes and feasible schedules before award.
"""
from pathlib import Path
from decimal import Decimal, ROUND_CEILING
import csv
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "outputs/tables/vehicle_budget_screen"
OUT = ROOT / "outputs/tables/seoul_cost_verification"
RAW = ROOT / "data/raw/drt_cost_evidence"
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)


def minimum_records(cost, benchmark):
    assert cost >= 0 and benchmark > 0
    return int((Decimal(str(cost))/Decimal(str(benchmark))).to_integral_value(rounding=ROUND_CEILING))


assert minimum_records(100, 25) == 4
assert minimum_records(101, 25) == 5
assert minimum_records(0, 25) == 0
benchmarks = {"published_calltaxi_average": 59700, "published_corporate_accessible_taxi_average": 44025}
budgets = list(csv.DictReader((PREVIOUS / "budget_scenarios.csv").open()))
capacities = list(csv.DictReader((PREVIOUS / "supplemental_service_capacity_scenarios.csv").open()))
assert len(budgets) == 18 and len(capacities) == 27
assert len({(r["cost_case"], r["option"], r["operating_slots"]) for r in budgets}) == 18
results = []
for budget in budgets:
    if budget["option"] != "existing_spare_vehicles_plus_staff":
        continue
    bought = next(r for r in budgets if r["cost_case"] == budget["cost_case"]
                  and r["operating_slots"] == budget["operating_slots"] and r["option"] == "new_vehicles_plus_staff")
    for capacity in capacities:
        if capacity["operating_slots"] != budget["operating_slots"]:
            continue
        slots = int(budget["operating_slots"])
        recurring = int(budget["annual_recurring_krw"])
        throughput = float(capacity["annual_record_handling_equivalent"])
        expected = slots*5*365*60*float(capacity["utilization_assumed"])/(float(capacity["observed_mean_medical_job_min"])+float(capacity["extra_minutes_assumed"]))
        assert abs(throughput-expected) < 1e-8
        row = {"cost_case": budget["cost_case"], "slots": slots,
               "assumed_extra_minutes": float(capacity["extra_minutes_assumed"]),
               "assumed_utilization": float(capacity["utilization_assumed"]),
               "capacity_equivalent_not_demand": throughput,
               "annual_recurring_assumption_krw": recurring,
               "recurring_krw_per_capacity_equivalent": recurring/throughput,
               "first_year_existing_cash_per_equivalent": int(budget["first_year_krw"])/throughput,
               "first_year_purchase_cash_per_equivalent": int(bought["first_year_krw"])/throughput}
        for label, value in benchmarks.items():
            row[label+"_krw"] = value
            row[label+"_minimum_records"] = minimum_records(recurring, value)
            row[label+"_recurring_screen_pass"] = recurring/throughput <= value
            row[label+"_max_average_cost_envelope_krw"] = throughput*value
        results.append(row)
assert len(results) == 81
central = [r for r in results if r["cost_case"] == "central_assumption" and r["assumed_extra_minutes"] == 10 and r["assumed_utilization"] == .7]
assert len(central) == 3
assert all(not r[label+"_recurring_screen_pass"] for r in central for label in benchmarks)
assert round((59700-44025)/59700*100, 1) == 26.3
for name, rows in [("scenario_grid.csv", results), ("central_case.csv", central)]:
    with (OUT / name).open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
sources = []
for src, name, url, page in [
    ("/tmp/seoul-2025-transport-budget-review.pdf", "seoul_2025_budget_review.pdf", "https://ms.smc.seoul.kr/record/appendixDownload.do?key=79b7b2ad9eef23597c28c9c44b07a568fa0b8c34f1ccf463bedb55134235d4cc30a66fa033baa1d3", 56),
    ("/tmp/seoul-bus-2024-settlement.pdf", "seoul_bus_2024_settlement.pdf", "https://mas.smc.seoul.kr/attach/record/SEOUL/appendix/a11/A0071195.pdf?time=20260622153142", 4)]:
    dest = RAW / name
    if not dest.exists():
        if not Path(src).exists():
            raise FileNotFoundError(f"Download {url} to {dest}")
        shutil.copyfile(src, dest)
    assert dest.read_bytes().startswith(b"%PDF")
    sources.append({"path": str(dest.relative_to(ROOT)), "source_url": url, "pdf_page": page,
                    "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
meta = {"checked_on": "2026-10-18", "sources": sources,
        "upstream_inputs": [str((PREVIOUS / f).relative_to(ROOT)) for f in ["budget_scenarios.csv", "supplemental_service_capacity_scenarios.csv", "assumptions.json"]],
        "benchmarks": benchmarks, "grid_rows": len(results),
        "grid_pass_counts_not_probabilities": {label: sum(r[label+"_recurring_screen_pass"] for r in results) for label in benchmarks},
        "decision": "Existing central illustrative 1–3 slot scenarios fail both published average-cost screens; new DRT cost superiority is not verified",
        "scope": "Annual recurring cost divided by capacity equivalent, not realized rides or quotes; excludes purchase and some support costs; first-year cash shown separately, not lifecycle expense",
        "break_even": "Minimum integer records for cost per record <= benchmark; does not establish marginal cash savings",
        "same_service_verified": False,
        "limitations": ["2024-era citywide comparator, not current three-district marginal cost", "No local DRT quote", "No identified vehicles or feasible shift roster", "No measured demand served by DRT", "No measured pooling or arrival-time improvement", "No comparable bus increment or route-extension cost", "81-grid pass counts are parameter coverage, not probabilities"]}
(OUT / "verification_manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
print(json.dumps({"central": central, "pass_counts": meta["grid_pass_counts_not_probabilities"]}, ensure_ascii=False, indent=2))
