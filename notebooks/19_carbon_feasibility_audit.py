"""Audit measured passenger distances; distinguish them from unobserved carbon reduction."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/calltaxi/seoul_calltaxi_2025.csv"
OUT = ROOT / "outputs/tables/carbon_audit"
OUT.mkdir(parents=True, exist_ok=True)
DISTRICTS = ["중구", "성동구", "동대문구"]
TIMES = ["접수일시", "예정일시", "배차일시", "승차일시", "하차일시", "취소일시"]


def summarize(frame, label):
    distance = frame["distance_m"]
    valid = distance.notna() & np.isfinite(distance) & distance.gt(0)
    positive = distance[valid]
    return {"cohort": label, "records": len(frame), "positive_distance_records": int(valid.sum()),
            "missing_or_nonfinite_distance_records": int((distance.isna() | ~np.isfinite(distance)).sum()),
            "zero_distance_records": int(distance.eq(0).sum()), "negative_distance_records": int(distance.lt(0).sum()),
            "recorded_passenger_km": float(positive.sum()/1000),
            "median_positive_distance_km": float(positive.median()/1000),
            "p99_positive_distance_km": float(positive.quantile(.99)/1000),
            "max_positive_distance_km": float(positive.max()/1000),
            "speed_over90_or_zero_duration_positive_records": int((valid & (frame.ride_min.le(0) | (distance/1000/frame.ride_min*60).gt(90))).sum()),
            "boundary": "positive recorded onboard distances only; not total vehicle-km or total passenger-km under pooling"}


def carbon_from_net_km(net_km, efficiency_km_per_l, factor_kg_per_l):
    if not np.isfinite([net_km, efficiency_km_per_l, factor_kg_per_l]).all() or efficiency_km_per_l <= 0 or factor_kg_per_l <= 0:
        raise ValueError("Finite inputs and positive efficiency/factor required")
    return net_km / efficiency_km_per_l * factor_kg_per_l


assert carbon_from_net_km(1000, 10, 2.6) == 260
assert carbon_from_net_km(-1000, 10, 2.6) == -260
assert carbon_from_net_km(0, 10, 2.6) == 0
try:
    carbon_from_net_km(1000, 0, 2.6)
except ValueError:
    pass
else:
    raise AssertionError("Zero efficiency must be rejected")

assert SOURCE.stat().st_size == 338587487
rows = 0
normal_parts, main_parts = [], []
for chunk in pd.read_csv(SOURCE, encoding="utf-8-sig", dtype=str, chunksize=200000):
    rows += len(chunk)
    for col in TIMES:
        chunk[col] = pd.to_datetime(chunk[col], format="mixed", errors="coerce")
    clean = chunk[TIMES[:5]].notna().all(axis=1) & chunk["취소일시"].isna()
    clean &= chunk["접수일시"].le(chunk["배차일시"]) & chunk["배차일시"].le(chunk["승차일시"]) & chunk["승차일시"].le(chunk["하차일시"])
    frame = chunk.loc[clean].copy()
    frame["distance_m"] = pd.to_numeric(frame["승차거리"], errors="coerce")
    frame["ride_min"] = (frame["하차일시"]-frame["승차일시"]).dt.total_seconds()/60
    frame["district"] = frame["출발구"].str.strip()
    frame["request_to_board_min"] = (frame["승차일시"]-frame["접수일시"]).dt.total_seconds()/60
    purpose = frame["이용목적"].str.strip()
    lead = (frame["예정일시"]-frame["접수일시"]).dt.total_seconds()/60
    main = purpose.str.contains("치료|재활", na=False) & ~purpose.str.contains("예약", na=False) & lead.between(0,1) & frame.district.isin(DISTRICTS)
    keep = ["distance_m", "ride_min", "district", "request_to_board_min", "차량구분"]
    part = frame.loc[main, keep].copy()
    part["hour"] = frame.loc[main,"예정일시"].dt.hour
    part["month"] = frame.loc[main,"예정일시"].dt.strftime("%Y-%m")
    main_parts.append(part)
    normal_parts.append(frame[keep])
assert rows == 1729476
normal = pd.concat(normal_parts,ignore_index=True)
main = pd.concat(main_parts,ignore_index=True)
assert len(normal)==1483321 and len(main)==6683
assert int(main.request_to_board_min.gt(60).sum())==1374
summaries = [summarize(normal,"all_normal_completed"), summarize(main,"three_district_treatment_main")]
for d in DISTRICTS:
    summaries.append(summarize(main[main.district.eq(d)],d))
for label,mask in [("morning_07_09",main.hour.between(7,9)),("over60_minutes",main.request_to_board_min.gt(60))]:
    summaries.append(summarize(main[mask],label))
assert sum(r["records"] for r in summaries[2:5])==6683
assert np.isclose(sum(r["recorded_passenger_km"] for r in summaries[2:5]),summaries[1]["recorded_passenger_km"])
speed_flag = main.distance_m.gt(0) & (main.ride_min.le(0) | (main.distance_m/1000/main.ride_min*60).gt(90))
summaries.append(summarize(main[~speed_flag],"main_excluding_speed_flags_sensitivity"))
pd.DataFrame(summaries).to_csv(OUT/"distance_audit.csv",index=False)
main.groupby("차량구분",dropna=False).agg(records=("distance_m","size"), recorded_distance_m=("distance_m","sum")).reset_index().to_csv(OUT/"main_vehicle_labels.csv",index=False)
monthly = main.groupby("month").agg(records=("distance_m","size"), positive_distance_records=("distance_m",lambda x:x.gt(0).sum()), positive_distance_m=("distance_m",lambda x:x[x.gt(0)].sum())).reset_index()
assert monthly.records.sum()==6683
assert np.isclose(monthly.positive_distance_m.sum()/1000,summaries[1]["recorded_passenger_km"])
monthly.to_csv(OUT/"monthly_recorded_distance.csv",index=False)
scenarios=[]
for net_km in [-1000,0,1000]:
    for efficiency in [8,10,12]:
        scenarios.append({"assumed_net_avoided_vehicle_km":net_km,"assumed_diesel_efficiency_km_per_l":efficiency,
                          "illustrative_factor_kg_per_l":2.6,"conditional_change_tonnes":carbon_from_net_km(net_km,efficiency,2.6)/1000,
                          "status":"conditional arithmetic only; neither distance reduction nor fleet fuel/efficiency observed"})
pd.DataFrame(scenarios).to_csv(OUT/"conditional_conversion_NOT_observed_reduction.csv",index=False)
fields = [{"field":k,"available_in_source":k in pd.read_csv(SOURCE,nrows=0).columns} for k in ["승차거리","차량번호","공차거리","총주행거리","연료종류","주유량","충전량"]]
pd.DataFrame(fields).to_csv(OUT/"field_availability.csv",index=False)
metadata={"checked_on":"2026-10-19","source":"https://www.data.go.kr/data/15115859/fileData.do", "distance_unit":"metres; confirmed in official metadata", "sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "actual_carbon_reduction_tonnes":None,"empirically_identified":False,
          "missing":["total/deadhead vehicle distance","measured fuel/energy by vehicle","vehicle identifiers/fuel type","post-intervention operations","comparable counterfactual service"],
          "cannot_infer":["waiting minutes as idling minutes","onboard distance as total vehicle distance","taxi or bus substitution from telecom OD","DRT adoption as measured carbon reduction"],
          "factor_source":"Environment Ministry carbon-neutral practice guide, school edition, household calculation worksheet: diesel 2.6 kgCO2eq/L; historical simple conversion, not verified 2025 fleet factor",
          "factor_pdf_page":45,
          "factor_reference":"https://me.go.kr/home/file/readDownloadFile2.do?fileId=286624&fileName=9b21fa71bd0607a9fb18f2223238c25270c07f988a98c05a1a9b6b78a411fc1c&fileSeq=1&openYn=Y",
          "decision":"Observed distance baseline is available; causal carbon reduction cannot be estimated from supplied records. Conditional examples must not be presented as empirical savings."}
(OUT/"carbon_identification_audit.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
print(pd.DataFrame(summaries).to_string(index=False))
