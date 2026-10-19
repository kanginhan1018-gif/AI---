"""Audit actual 2025 call-taxi records and summarize recorded service intervals.

Public file 15115859. This is not a complete request register or an age-specific
sample; timestamp differences are not automatically experienced waiting time.
"""
# %%
from pathlib import Path
import hashlib
import json
import os

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/calltaxi/seoul_calltaxi_2025.csv"
OUT = ROOT / "outputs/tables/calltaxi"
OUT.mkdir(parents=True, exist_ok=True)
TIMES = ["접수일시", "예정일시", "배차일시", "승차일시", "하차일시", "취소일시"]
CATEGORIES = ["출발구", "출발동", "목적구", "목적동", "이용목적", "차량구분", "장애유형"]
PILOT = ["중구", "성동구", "동대문구"]
METRICS = ["request_to_board_min", "schedule_to_board_min", "dispatch_to_board_min", "ride_min"]


def intervals(frame):
    result = frame[CATEGORIES].copy()
    for name, begin, end in [
        ("request_to_dispatch_min", "접수일시", "배차일시"),
        ("request_to_cancel_min", "접수일시", "취소일시"),
        ("request_to_board_min", "접수일시", "승차일시"),
        ("schedule_to_board_min", "예정일시", "승차일시"),
        ("dispatch_to_board_min", "배차일시", "승차일시"),
        ("ride_min", "승차일시", "하차일시"),
        ("schedule_lead_min", "접수일시", "예정일시"),
    ]:
        result[name] = (frame[end] - frame[begin]).dt.total_seconds() / 60
    result["scheduled_date"] = frame["예정일시"].dt.normalize()
    result["scheduled_time"] = frame["예정일시"]
    result["scheduled_hour"] = frame["예정일시"].dt.hour
    result["month"] = frame["예정일시"].dt.strftime("%Y-%m")
    for column, label in [("배차일시", "dispatch"), ("승차일시", "board"), ("하차일시", "alight"), ("취소일시", "cancel")]:
        result["has_" + label] = frame[column].notna()
    result["reservation_purpose_label"] = frame["이용목적"].str.contains("예약", na=False)
    result["request_equals_schedule"] = frame["접수일시"].notna() & frame["접수일시"].eq(frame["예정일시"])
    for label, begin, end in [
        ("dispatch_before_request", "접수일시", "배차일시"),
        ("board_before_dispatch", "배차일시", "승차일시"),
        ("alight_before_board", "승차일시", "하차일시"),
        ("cancel_before_request", "접수일시", "취소일시"),
    ]:
        result[label] = frame[end].lt(frame[begin])
    result["clean_completed"] = (
        frame[TIMES[:5]].notna().all(axis=1)
        & ~result.has_cancel & ~result.dispatch_before_request
        & ~result.board_before_dispatch & ~result.alight_before_board
    )
    return result


def self_check():
    # An advance booking must not turn a 10-minute schedule difference into a 70-minute wait.
    example = pd.DataFrame({column: ["test", "test", "test"] for column in CATEGORIES})
    dates = {
        "접수일시": ["2025-01-01 08:00", "2025-01-01 08:00", "2025-01-01 08:00"],
        "예정일시": ["2025-01-01 09:00", "2025-01-01 08:00", "2025-01-01 08:00"],
        "배차일시": ["2025-01-01 09:00", "2025-01-01 08:10", "2025-01-01 08:10"],
        "승차일시": ["2025-01-01 09:10", None, "2025-01-01 08:05"],
        "하차일시": ["2025-01-01 09:30", None, "2025-01-01 08:30"],
        "취소일시": [None, "2025-01-01 08:15", None],
    }
    for name, values in dates.items():
        example[name] = pd.to_datetime(values, format="mixed")
    result = intervals(example)
    assert result.loc[0, "request_to_board_min"] == 70
    assert result.loc[0, "schedule_to_board_min"] == 10
    assert result.loc[0, "request_to_dispatch_min"] == 60
    assert result.clean_completed.tolist() == [True, False, False]
    assert pd.isna(result.loc[1, "request_to_board_min"])


self_check()
assert SOURCE.stat().st_size == 338587487, "Download differs from the official Content-Length"
frames, hashes, audit = [], [], []
offset = 0
for chunk in pd.read_csv(SOURCE, encoding="utf-8-sig", dtype=str, chunksize=200_000):
    assert set(chunk.columns) == set(TIMES + CATEGORIES + ["요금", "승차거리"])
    hashes.append(pd.util.hash_pandas_object(chunk, index=False).to_numpy())
    item = {"first_source_row": offset + 1, "rows": len(chunk)}
    for column in chunk:
        item["missing_" + column] = int(chunk[column].isna().sum())
    for column in TIMES:
        parsed = pd.to_datetime(chunk[column], format="mixed", errors="coerce")
        item["unparseable_" + column] = int((chunk[column].notna() & parsed.isna()).sum())
        chunk[column] = parsed
    item["scheduled_outside_2025"] = int((chunk["예정일시"].notna() & ~chunk["예정일시"].dt.year.eq(2025)).sum())
    for column in CATEGORIES:
        chunk[column] = chunk[column].str.strip()
    frames.append(intervals(chunk))
    audit.append(item)
    offset += len(chunk)
    print(f"Parsed {offset:,} records", flush=True)

assert offset == 1_729_476, "Row count differs from official metadata"
data = pd.concat(frames, ignore_index=True)
unique_hashes = np.unique(np.concatenate(hashes))
hash_repeat_rows = offset - len(unique_hashes)
pd.DataFrame(audit).to_csv(OUT / "input_quality_by_chunk.csv", index=False)
data[["has_dispatch", "has_board", "has_alight", "has_cancel"]].value_counts(dropna=False).rename("records").reset_index().to_csv(OUT / "timestamp_presence_patterns.csv", index=False)
data.groupby(["request_equals_schedule", "reservation_purpose_label"], dropna=False).size().rename("records").reset_index().to_csv(OUT / "schedule_label_groups.csv", index=False)
assert data.scheduled_date.nunique() == 365


def summarize(frame, keys):
    """Record counts plus moments of the explicitly defined clean-completion cohort."""
    total = frame.groupby(keys, dropna=False).agg(
        published_records=("clean_completed", "size"),
        clean_completed_records=("clean_completed", "sum"),
        records_with_board_time=("has_board", "sum"),
        records_with_cancel_time=("has_cancel", "sum"),
        equal_request_schedule_records=("request_equals_schedule", "sum"),
    ).reset_index()
    valid = frame[frame.clean_completed]
    stats = valid.groupby(keys, dropna=False).agg(
        request_board_median_min=("request_to_board_min", "median"),
        request_board_p90_min=("request_to_board_min", lambda s: s.quantile(.9)),
        scheduled_board_mean_min=("schedule_to_board_min", "mean"),
        scheduled_board_median_min=("schedule_to_board_min", "median"),
        scheduled_board_p90_min=("schedule_to_board_min", lambda s: s.quantile(.9)),
        scheduled_board_after_60min_records=("schedule_to_board_min", lambda s: int(s.gt(60).sum())),
        scheduled_board_before_schedule_records=("schedule_to_board_min", lambda s: int(s.lt(0).sum())),
        dispatch_board_median_min=("dispatch_to_board_min", "median"),
    ).reset_index()
    same_time = valid[valid.request_equals_schedule & ~valid.reservation_purpose_label]
    subset = same_time.groupby(keys, dropna=False).agg(
        equal_time_nonreservation_completed=("request_to_board_min", "size"),
        equal_time_request_board_median_min=("request_to_board_min", "median"),
        equal_time_request_board_p90_min=("request_to_board_min", lambda s: s.quantile(.9)),
    ).reset_index()
    result = total.merge(stats, on=keys, how="left", validate="one_to_one").merge(subset, on=keys, how="left", validate="one_to_one")
    # Missing interval quantiles stay missing for groups without valid completions.
    return result


data["scope"] = "all_published_records"
annual = summarize(data, ["scope"])
annual.to_csv(OUT / "annual_record_intervals.csv", index=False)
summarize(data, ["month"]).to_csv(OUT / "monthly_record_intervals.csv", index=False)
districts = summarize(data, ["출발구"])
districts.to_csv(OUT / "origin_district_record_intervals.csv", index=False)
pilot = data[data["출발구"].isin(PILOT)].copy()
summarize(pilot, ["출발구", "출발동"]).to_csv(OUT / "pilot_original_dong_intervals.csv", index=False)
summarize(pilot, ["출발구", "scheduled_hour"]).to_csv(OUT / "pilot_scheduled_hour_intervals.csv", index=False)
pilot.groupby(["출발구", "출발동", "목적구", "목적동"], dropna=False).size().rename("published_records").reset_index().sort_values("published_records", ascending=False).to_csv(OUT / "pilot_original_label_od_counts.csv", index=False)
pilot.groupby(["출발구", "장애유형", "차량구분"], dropna=False).size().rename("published_records").reset_index().to_csv(OUT / "pilot_disability_vehicle_counts.csv", index=False)

# Broad lexical groups avoid forcing ambiguous historical administrative labels.
def broad_area(district, dong):
    result = pd.Series("other", index=district.index)
    for prefix in ["전농", "답십리", "장안"]:
        result.loc[district.eq("동대문구") & dong.str.startswith(prefix, na=False)] = prefix + "계열"
    result.loc[district.eq("중구") & (dong.str.startswith("신당", na=False) | dong.isin(["약수동", "다산동", "청구동", "동화동"]))] = "신당계열"
    return result


data["origin_area"] = broad_area(data["출발구"], data["출발동"])
data["destination_area"] = broad_area(data["목적구"], data["목적동"])
areas = summarize(data[~data.origin_area.eq("other")], ["origin_area"])
areas.to_csv(OUT / "candidate_broad_origin_areas.csv", index=False)
data.groupby(["출발구", "출발동", "origin_area"], dropna=False).size().rename("published_records").reset_index().to_csv(OUT / "original_label_area_review.csv", index=False)
corridors = []
for label, first, second in [("전농계열 내부", "전농계열", "전농계열"), ("답십리계열–장안계열", "답십리계열", "장안계열"), ("신당계열 내부", "신당계열", "신당계열")]:
    mask = (data.origin_area.eq(first) & data.destination_area.eq(second)) | (data.origin_area.eq(second) & data.destination_area.eq(first))
    part = data[mask].assign(corridor=label)
    corridors.append(summarize(part, ["corridor"]))
corridors = pd.concat(corridors, ignore_index=True)
corridors.to_csv(OUT / "candidate_broad_corridors.csv", index=False)

# Audit time ordering and preserve source-label geography rather than asserting a crosswalk.
quality = {
    "rows": offset, "scheduled_dates": data.scheduled_date.nunique(),
    "repeated_full_row_hashes": hash_repeat_rows,
    "timestamp_order_counts": {name: int(data[name].sum()) for name in ["dispatch_before_request", "board_before_dispatch", "alight_before_board", "cancel_before_request"]},
    "clean_completed_records": int(data.clean_completed.sum()),
    "original_15_columns": TIMES + CATEGORIES + ["요금", "승차거리"],
}
assert int(districts.published_records.sum()) == offset
assert int(annual.clean_completed_records.iloc[0]) == int(data.clean_completed.sum())
assert data.loc[data.clean_completed, ["request_to_board_min", "dispatch_to_board_min", "ride_min"]].ge(0).all().all()
with SOURCE.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
manifest = {
    "retrieved_on": "2026-10-18", "source": str(SOURCE.relative_to(ROOT)), "bytes": SOURCE.stat().st_size,
    "sha256": digest, "metadata_url": "https://www.data.go.kr/data/15115859/fileData.do",
    "download_url": "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003648626&fileDetailSn=1&insertDataPrcus=N",
    "quality": quality,
    "scope": "2025 scheduled-date records as published; not a verified all-request register",
    "clean_cohort": "First five timestamps present; no cancellation timestamp; request <= dispatch <= board <= alight",
    "equal_time_subset": "Clean cohort with request==scheduled and purpose lacking 예약; a record-defined subset, not a validated immediate-request flag",
    "geography": "Raw names retained; broad prefix groups only; historical names cannot be unambiguously joined to 2026 telecom administrative codes",
    "limitations": ["No age or person identifier", "Cancellation reasons and all-request denominator unavailable", "Scheduled timestamp meaning needs operational confirmation", "No direct measurement of general-bus accessibility or unrecorded abandoned trips", "2025 service vs 2026 telecom are separate periods"],
}
(OUT / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=int))
print("ANNUAL\n", annual.round(2).to_string(index=False))
print("BROAD AREAS\n", areas.round(2).to_string(index=False))
print("BROAD CORRIDORS\n", corridors.round(2).to_string(index=False))
print("QUALITY\n", json.dumps(quality, ensure_ascii=False, default=int))

# %% A static, reviewable distribution; no arbitrary exclusion of long delays.
os.environ.setdefault("MPLCONFIGDIR", "/tmp/drt-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

subset = data[data.clean_completed & data.request_equals_schedule & ~data.reservation_purpose_label]
fig, ax = plt.subplots(figsize=(10, 5))
for district, label, style in [("중구", "Jung", "-"), ("성동구", "Seongdong", "--"), ("동대문구", "Dongdaemun", ":")]:
    values = np.sort(subset.loc[subset["출발구"].eq(district), "request_to_board_min"].to_numpy())
    assert len(values)
    ax.plot(values, np.arange(1, len(values) + 1) / len(values), style, label=f"{label} (n={len(values):,})")
ax.set(xlabel="Request-to-boarding interval (minutes)", ylabel="Cumulative share", title="2025 call-taxi records | request equals scheduled time; no reservation purpose label", xlim=(0, None), ylim=(0, 1))
ax.legend()
ax.grid(alpha=.2)
fig.tight_layout()
fig.savefig(ROOT / "outputs/figures/calltaxi_2025_intervals.png", dpi=160)
plt.close(fig)
print("Source coverage, timestamp, grouping and interval checks passed.")
