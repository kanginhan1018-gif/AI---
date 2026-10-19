"""Reconcile existing treatment records and compare scheduled-hour bands.

These are completed service records, not unique people or DRT demand.
"""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/tables/public_service_necessity"
OUT = ROOT / "outputs/tables/seoul_drt_policy"
OUT.mkdir(parents=True, exist_ok=True)


def band(hour):
    if 7 <= hour < 10:
        return "07:00–09:59"
    if 10 <= hour < 15:
        return "10:00–14:59"
    if 15 <= hour < 18:
        return "15:00–17:59"
    return "other_hours"


assert [band(h) for h in [6, 7, 9, 10, 14, 15, 17, 18]] == [
    "other_hours", "07:00–09:59", "07:00–09:59", "10:00–14:59",
    "10:00–14:59", "15:00–17:59", "15:00–17:59", "other_hours"]
hours = list(csv.DictReader((SOURCE / "treatment_hour_diagnostic.csv").open()))
annual = [r for r in csv.DictReader((SOURCE / "purpose_burden_annual.csv").open())
          if r["purpose_group"] == "explicit_treatment_rehab" and r["cohort"] == "within_1min" and r["district"] != "ALL"]
assert len(annual) == 3
assert len({(r["district"], r["scheduled_hour"]) for r in hours}) == len(hours)
for district in annual:
    matching = [r for r in hours if r["district"] == district["district"]]
    for key in ["records", "over_60_records", "over_90_records"]:
        assert sum(int(r[key]) for r in matching) == int(district[key])
results = []
for district in [r["district"] for r in annual] + ["three_districts"]:
    selected = [r for r in hours if district == "three_districts" or r["district"] == district]
    for label in ["07:00–09:59", "10:00–14:59", "15:00–17:59", "other_hours"]:
        rows = [r for r in selected if band(int(r["scheduled_hour"])) == label]
        n = sum(int(r["records"]) for r in rows)
        over = sum(int(r["over_60_records"]) for r in rows)
        assert 0 <= over <= n and n > 0
        results.append({"district": district, "scheduled_hour_band": label, "records": n,
                        "over_60_records": over, "over_60_pct": 100*over/n,
                        "queue_mean_min": sum(int(r["records"])*float(r["queue_mean_min"]) for r in rows)/n,
                        "pickup_mean_min": sum(int(r["records"])*float(r["pickup_mean_min"]) for r in rows)/n})
combined = [r for r in results if r["district"] == "three_districts"]
assert sum(r["records"] for r in combined) == 6683
assert sum(r["over_60_records"] for r in combined) == 1374
with (OUT / "treatment_timeband_burden.csv").open("w") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
(OUT / "analysis_manifest.json").write_text(json.dumps({
    "inputs": [str((SOURCE / f).relative_to(ROOT)) for f in ["treatment_hour_diagnostic.csv", "purpose_burden_annual.csv"]],
    "upstream_raw_analysis": "notebooks/12_public_service_necessity.py",
    "time_axis": "Scheduled timestamp hour, not appointment arrival hour; 0–1 minute scheduled-minus-request cohort",
    "bands": "Descriptive operational bands, not optimized intervention hours; every hour assigned exactly once",
    "limits": ["No pooled quantiles from subgroup quantiles", "Record-weighted means only", "No repeated-rider identification", "No causal inference about supply or DRT effects", "No assumption of daily or same-destination pooling"]
}, ensure_ascii=False, indent=2))
print(json.dumps(combined, ensure_ascii=False, indent=2))
