"""Assess observed essential-purpose service burden, not latent DRT demand."""
from pathlib import Path
import json
import runpy

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/tables/public_service_necessity"
OUT.mkdir(parents=True, exist_ok=True)
data = runpy.run_path(str(ROOT / "notebooks/10_calltaxi_service_evidence.py"))["data"]
PILOT = ["중구", "성동구", "동대문구"]


def purpose_group(values):
    # Other includes app/web calls; it must never become a nonessential label.
    return np.select([
        values.str.contains("치료|재활", na=False),
        values.str.contains("통학|출근", na=False),
        values.str.contains("귀가", na=False),
    ], ["explicit_treatment_rehab", "explicit_school_work", "return_home"], default="undetermined_or_other")


assert purpose_group(pd.Series(["예약치료", "재활", "통학/출근", "기타", None])).tolist() == [
    "explicit_treatment_rehab", "explicit_treatment_rehab", "explicit_school_work",
    "undetermined_or_other", "undetermined_or_other"]
data["purpose_group"] = purpose_group(data["이용목적"])
assert data.purpose_group.notna().all()
labels = data.groupby(["출발구", "이용목적", "purpose_group"], dropna=False).size().reset_index(name="published_records")
assert labels.published_records.sum() == len(data)
labels.to_csv(OUT / "purpose_label_audit.csv", index=False)


def summarize(rows):
    n = len(rows)
    result = {"records": n, "active_days": rows.scheduled_date.nunique(),
              "median_min": rows.request_to_board_min.median(),
              "p90_min": rows.request_to_board_min.quantile(.9),
              "queue_mean_min": rows.request_to_dispatch_min.mean(),
              "pickup_mean_min": rows.dispatch_to_board_min.mean()}
    for threshold in [30, 60, 90]:
        count = int(rows.request_to_board_min.gt(threshold).sum())
        result[f"over_{threshold}_records"] = count
        result[f"over_{threshold}_pct"] = 100 * count / n if n else np.nan
    return result


annual, monthly, hours, statuses = [], [], [], []
for district in ["ALL"] + PILOT:
    original = data if district == "ALL" else data[data["출발구"].eq(district)]
    for purpose in ["all", "explicit_treatment_rehab", "explicit_school_work", "return_home", "undetermined_or_other"]:
        base = original if purpose == "all" else original[original.purpose_group.eq(purpose)]
        statuses.append({"district": district, "purpose_group": purpose,
                         "published_records": len(base), "clean_completed": int(base.clean_completed.sum()),
                         "cancel_timestamp_records": int(base.has_cancel.sum()),
                         "other_not_clean_or_cancel": int((~base.clean_completed & ~base.has_cancel).sum())})
        for cohort, allowance in [("exact_equal", 0), ("within_1min", 1), ("within_5min", 5)]:
            part = base[base.clean_completed & ~base.reservation_purpose_label & base.schedule_lead_min.between(0, allowance)]
            assert part.request_to_board_min.ge(0).all()
            annual.append({"district": district, "purpose_group": purpose, "cohort": cohort, **summarize(part)})
            if purpose in ["all", "explicit_treatment_rehab"] and cohort != "within_5min":
                for month, rows in part.groupby("month"):
                    monthly.append({"district": district, "purpose_group": purpose, "cohort": cohort, "month": month, **summarize(rows)})
            if purpose == "explicit_treatment_rehab" and cohort == "within_1min" and district != "ALL":
                for hour, rows in part.groupby("scheduled_hour"):
                    hours.append({"district": district, "scheduled_hour": hour, **summarize(rows)})
annual, monthly, statuses = pd.DataFrame(annual), pd.DataFrame(monthly), pd.DataFrame(statuses)
for district in ["ALL"] + PILOT:
    for cohort in ["exact_equal", "within_1min", "within_5min"]:
        group = annual[annual.district.eq(district) & annual.cohort.eq(cohort)].set_index("purpose_group")
        assert group.loc["all", "records"] == group.drop(index="all").records.sum()
    for purpose in ["all", "explicit_treatment_rehab"]:
        for cohort in ["exact_equal", "within_1min"]:
            rows = monthly[monthly.district.eq(district) & monthly.purpose_group.eq(purpose) & monthly.cohort.eq(cohort)]
            total = annual[annual.district.eq(district) & annual.purpose_group.eq(purpose) & annual.cohort.eq(cohort)].iloc[0]
            assert rows.records.sum() == total.records
            assert rows.over_60_records.sum() == total.over_60_records
assert (statuses.published_records == statuses.clean_completed + statuses.cancel_timestamp_records + statuses.other_not_clean_or_cancel).all()
annual.to_csv(OUT / "purpose_burden_annual.csv", index=False)
monthly.to_csv(OUT / "purpose_burden_monthly.csv", index=False)
statuses.to_csv(OUT / "published_status_by_purpose.csv", index=False)
pd.DataFrame(hours).to_csv(OUT / "treatment_hour_diagnostic.csv", index=False)

# Check the local access proxy before using it to justify a geographic conclusion.
proxy = []
for code in ["11020", "11040", "11060"]:
    walk = pd.read_csv(ROOT / f"data/raw/dong_walk_input_{code}.csv")
    proxy.append({"district_code": code, "representative_dong_rows": len(walk),
                  "median_centroid_to_stop_straight_line_m": walk.distance_m.median(),
                  "maximum_centroid_to_stop_straight_line_m": walk.distance_m.max(),
                  "verified_pedestrian_paths": False, "essential_destinations_in_proxy": False,
                  "actual_lowfloor_departures_in_proxy": False})
pd.DataFrame(proxy).to_csv(OUT / "access_proxy_fitness.csv", index=False)
meta = {"source": "data/raw/calltaxi/seoul_calltaxi_2025.csv", "raw_records": len(data),
        "interpretation": "Observed service burden supports public-service improvement, not proven denial of access or DRT superiority",
        "classification": "Treatment/rehab and school/work are explicit labels only; unknown/other never assumed nonessential",
        "official_reply": "https://www.sisul.or.kr/open_content/main/qna/qnaMsgDetail.do?qnaid=QNAS20260908000002",
        "reply_date": "2026-09-09; explains published categories but does not prove all 2025 procedures identical",
        "thresholds": "30/60/90 minutes are descriptive sensitivity cuts, not legal service standards or appointment lateness",
        "unit": "records, not unique riders; completed-record intervals exclude cancellation outcomes",
        "comparison": "All published origin districts plus three pilots; no inference about all older residents",
        "access_proxy": "One representative dong centroid to nearest stop; straight-line distance and endpoint elevation difference, not pedestrian network",
        "existing_support": "outputs/tables/calltaxi_reassessment/common_mix_standardized_intervals.csv"}
(OUT / "analysis_manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
print("ANNUAL\n", annual[annual.purpose_group.isin(["all", "explicit_treatment_rehab"]) & annual.cohort.ne("within_5min")].round(2).to_string(index=False))
print("MONTHLY TREATMENT\n", monthly[monthly.purpose_group.eq("explicit_treatment_rehab") & monthly.cohort.eq("within_1min")].round(2).to_string(index=False))
print("STATUSES\n", statuses.to_string(index=False))
print("Purpose, numerator/denominator and monthly reconciliation checks passed.")
