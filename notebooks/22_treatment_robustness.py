"""Recompute sensitivity of treatment waiting-time findings from raw records.

All periods were already inspected; these are descriptive checks, not holdout validation.
"""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/raw/calltaxi/seoul_calltaxi_2025.csv"
OUT=ROOT/"outputs/tables/treatment_robustness"
OUT.mkdir(parents=True,exist_ok=True)
TIMES=["접수일시","예정일시","배차일시","승차일시","하차일시","취소일시"]
assert SOURCE.stat().st_size==338587487
parts=[];total=0
for chunk in pd.read_csv(SOURCE,dtype=str,encoding="utf-8-sig",chunksize=200000,usecols=TIMES+["출발구","이용목적","차량구분"]):
    total+=len(chunk)
    for col in TIMES:chunk[col]=pd.to_datetime(chunk[col],format="mixed",errors="coerce")
    valid=chunk[TIMES[:5]].notna().all(axis=1)&chunk["취소일시"].isna()
    valid &= chunk["접수일시"].le(chunk["배차일시"])&chunk["배차일시"].le(chunk["승차일시"])&chunk["승차일시"].le(chunk["하차일시"])
    valid &= chunk["출발구"].str.strip().isin(["중구","성동구","동대문구"])
    frame=chunk.loc[valid].copy()
    purpose=frame["이용목적"].str.strip()
    frame["treatment"]=purpose.str.contains("치료|재활",na=False)
    frame["reservation"]=purpose.str.contains("예약",na=False)
    frame["lead"]=(frame["예정일시"]-frame["접수일시"]).dt.total_seconds()/60
    frame["wait"]=(frame["승차일시"]-frame["접수일시"]).dt.total_seconds()/60
    frame["queue"]=(frame["배차일시"]-frame["접수일시"]).dt.total_seconds()/60
    frame["pickup"]=(frame["승차일시"]-frame["배차일시"]).dt.total_seconds()/60
    frame["scheduled_hour"]=frame["예정일시"].dt.hour
    frame["request_hour"]=frame["접수일시"].dt.hour
    frame["month"]=frame["예정일시"].dt.month
    frame["weekday"]=frame["예정일시"].dt.dayofweek
    parts.append(frame[["treatment","reservation","lead","wait","queue","pickup","scheduled_hour","request_hour","month","weekday","차량구분"]])
assert total==1729476
all_records=pd.concat(parts,ignore_index=True)
treatment=all_records[all_records.treatment & ~all_records.reservation]
main=treatment[treatment.lead.between(0,1)]
assert len(main)==6683 and main.wait.gt(60).sum()==1374
cases=[("주 분석 0~1분",main,"scheduled_hour"),
       ("예정−접수 0분",treatment[treatment.lead.eq(0)],"scheduled_hour"),
       ("예정−접수 0~5분",treatment[treatment.lead.between(0,5)],"scheduled_hour"),
       ("월~금 공휴일 포함",main[main.weekday.lt(5)],"scheduled_hour"),
       ("토·일",main[main.weekday.ge(5)],"scheduled_hour"),
       ("특장차만",main[main["차량구분"].str.strip().eq("특장차")],"scheduled_hour"),
       ("1~6월",main[main.month.le(6)],"scheduled_hour"),
       ("7~12월",main[main.month.ge(7)],"scheduled_hour"),
       ("접수시각 시간축",main,"request_hour"),
       ("비교용 전체 목적",all_records[~all_records.reservation & all_records.lead.between(0,1)],"scheduled_hour")]
rows=[]
for label,frame,hour in cases:
    assert len(frame)>0
    morning=frame[hour].between(7,9)
    midday=frame[hour].between(10,14)
    over60=frame.wait.gt(60);over90=frame.wait.gt(90)
    rows.append({"case":label,"records":len(frame),"over60_records":int(over60.sum()),"over60_pct":100*over60.mean(),
                 "morning_records":int(morning.sum()),"morning_over60_records":int((morning&over60).sum()),
                 "morning_over60_pct":100*over60[morning].mean(),
                 "midday_records":int(midday.sum()),"midday_over60_pct":100*over60[midday].mean(),
                 "morning_share_of_over60_pct":100*(morning&over60).sum()/over60.sum() if over60.any() else None,
                 "over90_records":int(over90.sum()),"over90_pct":100*over90.mean(),
                 "morning_share_of_over90_pct":100*(morning&over90).sum()/over90.sum() if over90.any() else None,
                 "p90_wait_min":frame.wait.quantile(.9),
                 "morning_queue_mean_min":frame.loc[morning,"queue"].mean(),
                 "midday_queue_mean_min":frame.loc[midday,"queue"].mean()})
result=pd.DataFrame(rows)
assert result.loc[0,"morning_over60_records"]==1148
assert sum(result.loc[result["case"].isin(["1~6월","7~12월"]),"records"])==6683
for col in ["records","over60_records","morning_records","morning_over60_records","over90_records"]:
    assert result.loc[result["case"].isin(["월~금 공휴일 포함","토·일"]),col].sum()==result.loc[0,col]
result.to_csv(OUT/"sensitivity_checks.csv",index=False)
(OUT/"scope.json").write_text(json.dumps({"source":str(SOURCE.relative_to(ROOT)),"raw_rows":total,
 "interpretation":"Descriptive sensitivity, not independent holdout, causal effect or unique-rider inference",
 "weekday_rule":"Monday-Friday including public holidays; not a statutory working-day calendar",
 "case_count":len(rows),"thresholds":"strictly greater than 60/90 minutes; descriptive, not legal standards"},ensure_ascii=False,indent=2))
print(result.round(3).to_string(index=False))
