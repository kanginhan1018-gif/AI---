"""Coarse same-destination co-occurrence screen; NOT feasible pooled trips.

Fixed time bins miss neighbours across bin edges. Dong labels are unreconciled;
no exact address, arrival deadline, rider ID or wheelchair/vehicle capacity is known.
"""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/shared_destination_screen'
OUT.mkdir(parents=True,exist_ok=True)
times=['접수일시','예정일시','배차일시','승차일시','하차일시','취소일시']
parts=[];total=0
for c in pd.read_csv(ROOT/'data/raw/calltaxi/seoul_calltaxi_2025.csv',dtype=str,encoding='utf-8-sig',chunksize=200000,
                     usecols=times+['출발구','출발동','목적구','목적동','이용목적']):
    total+=len(c)
    for col in times:c[col]=pd.to_datetime(c[col],format='mixed',errors='coerce')
    valid=c[times[:5]].notna().all(axis=1)&c['취소일시'].isna()
    valid &= c['접수일시'].le(c['배차일시'])&c['배차일시'].le(c['승차일시'])&c['승차일시'].le(c['하차일시'])
    purpose=c['이용목적'].str.strip()
    lead=(c['예정일시']-c['접수일시']).dt.total_seconds()/60
    valid &= lead.between(0,1)&purpose.str.contains('치료|재활',na=False)&~purpose.str.contains('예약',na=False)
    valid &= c['출발구'].str.strip().isin(['중구','성동구','동대문구'])
    f=c.loc[valid,['접수일시','출발구','출발동','목적구','목적동']].copy()
    for col in ['출발구','출발동','목적구','목적동']:f[col]=f[col].str.strip().replace('',pd.NA)
    parts.append(f)
data=pd.concat(parts,ignore_index=True)
assert total==1729476 and len(data)==6683
rows=[]
for minutes in [15,30,60]:
    for label,keys in [('same_destination_dong',['목적구','목적동']),
                       ('same_origin_district_destination_dong',['출발구','목적구','목적동']),
                       ('same_origin_dong_destination_dong',['출발구','출발동','목적구','목적동'])]:
        f=data.dropna(subset=keys).copy()
        f['slot']=f['접수일시'].dt.floor(f'{minutes}min')
        bins=f.groupby(keys+['slot']).size()
        assert bins.sum()==len(f)
        repeated=bins[bins.ge(2)]
        count=int(repeated.sum())
        assert 0<=count<=len(f)<=6683
        rows.append({'screen':label,'fixed_bin_minutes':minutes,'cohort_records':6683,'complete_location_records':len(f),
                     'cooccurrence_groups':len(repeated),'records_in_2plus_groups':count,
                     'share_of_cohort_pct':100*count/6683,'maximum_group_size':int(bins.max())})
result=pd.DataFrame(rows)
for minutes in [15,30,60]:
    counts=result[result.fixed_bin_minutes.eq(minutes)].records_in_2plus_groups.tolist()
    assert counts==sorted(counts,reverse=True)
result.to_csv(OUT/'coarse_cooccurrence_NOT_FEASIBLE_POOLING.csv',index=False)
(OUT/'scope.json').write_text(json.dumps({'cohort':6683,'scope':'Three case origins; treatment/rehab clean completed; lead 0-1 min; request-time fixed bins',
 'warning':'Co-occurrence is neither distinct passengers nor same facility nor a feasible shared dispatch. No achievable cost/carbon reduction inferred.',
 'locations':'Published dong strings; no historical boundary reconciliation or exact addresses; no missing location imputation',
 'next_validation':'Exact pickup/dropoff, arrival window, consent, support and accessible seating constraints, route detour and baseline comparison'},ensure_ascii=False,indent=2))
print(result.round(3).to_string(index=False))
