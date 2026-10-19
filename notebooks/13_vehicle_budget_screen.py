"""Observed workload diagnostics and explicitly hypothetical resource budgets.

No identified vehicles or shift roster: this is not a fleet optimization model.
"""
from pathlib import Path
import json
import math
import runpy

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/tables/vehicle_budget_screen"
OUT.mkdir(parents=True, exist_ok=True)
data = runpy.run_path(str(ROOT / "notebooks/10_calltaxi_service_evidence.py"))["data"]
PILOT = ["중구", "성동구", "동대문구"]
base = data[data.clean_completed & data["출발구"].isin(PILOT)].copy()
base["explicit_medical"] = base["이용목적"].str.contains("치료|재활", na=False)
base["observed_job_min"] = base.dispatch_to_board_min + base.ride_min
assert base.observed_job_min.ge(0).all()
assert len(base[base.explicit_medical]) == 9472


def required_staff(vehicle_slots, hours_per_day, days, annual_coverage_hours):
    assert vehicle_slots >= 0 and hours_per_day > 0 and days > 0 and annual_coverage_hours > 0
    return math.ceil(vehicle_slots * hours_per_day * days / annual_coverage_hours)


def budget(slots, new_vehicles, staff_cost, vehicle_cost, annual_vehicle_cost,
           annual_dispatch_cost=10_000_000, setup_cost=20_000_000):
    assert 0 <= new_vehicles <= slots
    staff = required_staff(slots, 5, 365, 1500)
    recurring = staff * staff_cost + slots * annual_vehicle_cost + annual_dispatch_cost
    return {"operating_slots": slots, "new_vehicles": new_vehicles, "staff_coverage_screen": staff,
            "annual_covered_vehicle_hours": slots * 5 * 365,
            "annual_recurring_krw": recurring,
            "initial_vehicle_purchase_krw": new_vehicles * vehicle_cost,
            "initial_setup_krw": setup_cost,
            "first_year_krw": recurring + new_vehicles * vehicle_cost + setup_cost}


assert required_staff(0, 5, 365, 1500) == 0
assert required_staff(3, 5, 365, 1500) == 4
fixture = budget(1, 1, 60_000_000, 80_000_000, 15_000_000)
assert fixture["first_year_krw"] == 245_000_000
assert budget(3, 3, 60_000_000, 80_000_000, 15_000_000)["first_year_krw"] - budget(3, 0, 60_000_000, 80_000_000, 15_000_000)["first_year_krw"] == 240_000_000

summary, hourly, screens = [], [], []
grid = pd.date_range("2025-01-01", "2026-01-01", freq="h", inclusive="left")
assert len(grid) == 8760
for scope in ["three_districts_pooled"] + PILOT:
    original = base if scope == "three_districts_pooled" else base[base["출발구"].eq(scope)]
    for purpose, part in [("all_completed", original), ("explicit_treatment_rehab", original[original.explicit_medical])]:
        summary.append({"scope": scope, "purpose": purpose, "records": len(part),
                        "pickup_median_min": part.dispatch_to_board_min.median(),
                        "ride_median_min": part.ride_min.median(),
                        "job_mean_min": part.observed_job_min.mean(),
                        "job_median_min": part.observed_job_min.median(),
                        "job_p90_min": part.observed_job_min.quantile(.9),
                        "job_p95_min": part.observed_job_min.quantile(.95),
                        "job_over_240_records": int(part.observed_job_min.gt(240).sum()),
                        "job_max_min": part.observed_job_min.max(),
                        "scheduled_08_to_18_records": int(part.scheduled_hour.between(8, 17).sum())})
        # Arrival-hour workload is not concurrent vehicle occupancy or a queueing simulation.
        grouped = part.groupby(part.scheduled_time.dt.floor("h")).agg(
            records=("observed_job_min", "size"), observed_job_min=("observed_job_min", "sum"))
        full = grouped.reindex(grid, fill_value=0)
        assert full.records.sum() == len(part)
        assert np.isclose(full.observed_job_min.sum(), part.observed_job_min.sum())
        full.index.name = "scheduled_hour_start"
        exported = full.reset_index().assign(scope=scope, purpose=purpose)
        hourly.append(exported)
        for prep in [0, 10, 20]:
            workload = full.observed_job_min + prep * full.records
            for hours_name, mask in [("all_24_hours", np.ones(len(full), dtype=bool)),
                                      ("08_to_18_only", (full.index.hour >= 8) & (full.index.hour < 18))]:
                selected = workload[mask]
                for utilization in [.6, .7, .8]:
                    screens.append({"scope": scope, "purpose": purpose, "hours": hours_name,
                                    "assumed_extra_min_per_record": prep, "assumed_utilization": utilization,
                                    "calendar_hour_bins": len(selected), "mean_hour_work_min": selected.mean(),
                                    "p95_hour_work_min": selected.quantile(.95),
                                    "max_hour_work_min": selected.max(),
                                    "p95_load_equivalent_slots": math.ceil(selected.quantile(.95) / 60 / utilization)})

summary = pd.DataFrame(summary)
summary.to_csv(OUT / "observed_service_cycle.csv", index=False)
pd.concat(hourly, ignore_index=True).to_csv(OUT / "calendar_hour_workload.csv", index=False)
pd.DataFrame(screens).to_csv(OUT / "load_equivalent_sensitivity.csv", index=False)

# Monetary values below are unquoted planning assumptions, not market estimates.
cost_cases = [("low_assumption", 50_000_000, 70_000_000, 10_000_000),
              ("central_assumption", 60_000_000, 80_000_000, 15_000_000),
              ("high_assumption", 70_000_000, 100_000_000, 20_000_000)]
budgets, capacity = [], []
medical_cycle = base[base.explicit_medical].observed_job_min.mean()
for slots in [1, 2, 3]:
    for name, wage, purchase, vehicle_annual in cost_cases:
        for option, bought in [("existing_spare_vehicles_plus_staff", 0), ("new_vehicles_plus_staff", slots)]:
            row = {"cost_case": name, "option": option,
                   "assumed_staff_full_cost_krw": wage, "assumed_vehicle_purchase_krw": purchase,
                   "assumed_vehicle_annual_cost_krw": vehicle_annual,
                   **budget(slots, bought, wage, purchase, vehicle_annual)}
            budgets.append(row)
    for prep in [0, 10, 20]:
        for utilization in [.6, .7, .8]:
            capacity.append({"operating_slots": slots, "hours_per_day_assumed": 5, "days_assumed": 365,
                             "extra_minutes_assumed": prep, "utilization_assumed": utilization,
                             "observed_mean_medical_job_min": medical_cycle,
                             "annual_record_handling_equivalent": slots * 5 * 365 * 60 * utilization / (medical_cycle + prep)})
pd.DataFrame(budgets).to_csv(OUT / "budget_scenarios.csv", index=False)
pd.DataFrame(capacity).to_csv(OUT / "supplemental_service_capacity_scenarios.csv", index=False)
assumptions = {
    "observed": {"source": "2025 calltaxi CSV; reuse notebook 10 chronology rules", "medical_completed_records": 9472,
                 "job_minutes": "dispatch-to-board + board-to-alight; independent record service assumption"},
    "not_observed": ["vehicle IDs", "driver shifts", "fleet availability", "post-dropoff support and recovery time",
                     "all failed requests and causes", "wheelchair occupancy", "procurement quotes", "supplemental service effects"],
    "load_screen": "P95 arrival-hour assigned workload / 60 / assumed utilization, rounded up; not simultaneous fleet need, not additional vehicles, not 95% on-time guarantee",
    "supplemental_scope": "1/2/3 simultaneously staffed slots, 5 hours daily, 365 days; illustrative addition to existing service, not full replacement",
    "staffing": "ceil(covered vehicle-hours / assumed 1500 annual coverage hours per staff); hour-balance screen only, not feasible shift roster",
    "money": "Low/central/high planning assumptions; NO verified quote. Staff annual full cost 50/60/70m KRW; purchase 70/80/100m; annual running cost per slot 10/15/20m; shared dispatch 10m/y; setup 20m",
    "cost_scope": "Gross scenario resource budgets, not verified incremental cash costs; existing budget overlaps unadjusted; no fare income, subsidy offsets, depreciation or financing; existing spare scenario requires suitable otherwise available vehicles; no dedicated attendant included",
    "capacity": "Handling equivalents, not additional riders or long waits avoided; medical label selection and supplied completed records only",
    "official_context": "https://mas.smc.seoul.kr/record/recordView.do?key=ac1d3b413cc627a01443d74b91d80acd66506869a7a8f887a511aeaf486cccf60eb951b4ecbefcb7",
}
(OUT / "assumptions.json").write_text(json.dumps(assumptions, ensure_ascii=False, indent=2))
print("OBSERVED\n", summary.round(2).to_string(index=False))
print("LOAD SCREEN\n", pd.DataFrame(screens).query("purpose == 'explicit_treatment_rehab' and assumed_extra_min_per_record == 10 and assumed_utilization == .7").round(2).to_string(index=False))
print("BUDGET CENTRAL\n", pd.DataFrame(budgets).query("cost_case == 'central_assumption'").to_string(index=False))
print("Arithmetic, cohort size and calendar-zero denominator checks passed.")
