"""Check broader pooling, unit-cost and vehicle-km claims without inventing uptake.

Observed cohorts remain mobility-service users, never the general population.
Telecom results describe flows, not people who will adopt DRT or change mode.
"""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/tables/open_pooling_verification'
OUT.mkdir(parents=True, exist_ok=True)
TIMES = ['접수일시','예정일시','배차일시','승차일시','하차일시','취소일시']
parts=[]; raw_rows=0
for c in pd.read_csv(ROOT/'data/raw/calltaxi/seoul_calltaxi_2025.csv', dtype=str,
                     encoding='utf-8-sig', chunksize=200000,
                     usecols=TIMES+['출발구','출발동','목적구','목적동','이용목적']):
    raw_rows += len(c)
    for col in TIMES:c[col]=pd.to_datetime(c[col], format='mixed', errors='coerce')
    purpose=c['이용목적'].str.strip()
    valid=c[TIMES[:5]].notna().all(axis=1)&c['취소일시'].isna()
    valid &= c['접수일시'].le(c['배차일시'])&c['배차일시'].le(c['승차일시'])&c['승차일시'].le(c['하차일시'])
    lead=(c['예정일시']-c['접수일시']).dt.total_seconds()/60
    valid &= lead.between(0,1)&~purpose.str.contains('예약',na=False)
    valid &= c['출발구'].str.strip().isin(['중구','성동구','동대문구'])
    f=c.loc[valid,['접수일시','출발구','출발동','목적구','목적동']].copy()
    for col in ['출발구','출발동','목적구','목적동']:f[col]=f[col].str.strip().replace('',pd.NA)
    f['treatment']=purpose.loc[valid].str.contains('치료|재활',na=False)
    parts.append(f)
data=pd.concat(parts,ignore_index=True)
assert raw_rows==1729476 and len(data)==100222 and data.treatment.sum()==6683
rows=[]
for cohort,original in [('treatment',data[data.treatment]),('all_purposes_same_service',data)]:
    for minutes,offset in [(15,0),(30,0),(30,15),(60,0)]:
        for name,keys in [('destination_dong',['목적구','목적동']),
                          ('origin_district_destination_dong',['출발구','목적구','목적동']),
                          ('origin_dong_destination_dong',['출발구','출발동','목적구','목적동'])]:
            f=original.dropna(subset=keys).copy()
            # Fixed bins retain exact dates; offsets expose a bin-boundary sensitivity.
            f['slot']=(f['접수일시']-pd.Timedelta(minutes=offset)).dt.floor(f'{minutes}min')
            bins=f.groupby(keys+['slot']).size()
            assert bins.sum()==len(f)
            repeated=bins[bins.ge(2)]
            rows.append({'cohort':cohort,'minutes':minutes,'bin_offset_minutes':offset,'screen':name,
                'records':len(original),'location_complete_records':len(f),'groups_2plus':len(repeated),
                'records_in_2plus':int(repeated.sum()),'share_pct':100*repeated.sum()/len(original),
                'status':'co-occurrence only, not distinct riders or feasible dispatch'})
coocc=pd.DataFrame(rows)
check=coocc[(coocc.cohort=='treatment')&(coocc.minutes==30)&(coocc.bin_offset_minutes==0)]
assert check.records_in_2plus.tolist()==[441,308,129]
coocc.to_csv(OUT/'service_cooccurrence.csv',index=False)

# Existing general-population OD aggregates; age expansion is NOT forecast take-up.
source=ROOT/'outputs/tables/telecom_12weeks/outbound_od_hour_mean_trips.csv'
compact=OUT/'general_population_OD_INPUT_ALL_ELIGIBLE.csv'
if source.exists():
    top_parts=[]
    for c in pd.read_csv(source,chunksize=150000):
        f=c[c.day_type.eq('weekday')&c.hour.between(7,9)&c.same_dong.eq(False)
            &c.destination_name.str.startswith('서울특별시 ',na=False)].copy()
        top_parts.append(f[['o_admdong_cd','d_admdong_cd','origin_name','destination_name','total_cnt','60plus_cnt']])
    f=pd.concat(top_parts,ignore_index=True)
    top=f.groupby(['o_admdong_cd','d_admdong_cd','origin_name','destination_name']).agg(
        all_age_mean_weekday_07_10_trips=('total_cnt','sum'),age60plus_mean_weekday_07_10_trips=('60plus_cnt','sum')).reset_index()
    top.to_csv(compact,index=False)
    telecom_source_hash=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
else:
    # shortcut: package reproduces from scoped aggregate; raw telecom validation requires 07 and its original files.
    prior=json.loads((OUT/'verification_scope.json').read_text())
    assert hashlib.file_digest(compact.open('rb'),'sha256').hexdigest()==prior['packaged_telecom_input_sha256']
    top=pd.read_csv(compact)
    telecom_source_hash=prior['general_population_source_sha256']
assert not top.duplicated(['o_admdong_cd','d_admdong_cd']).any()
assert top.all_age_mean_weekday_07_10_trips.ge(0).all()
top['all_age_to_age60plus_flow_ratio']=top.all_age_mean_weekday_07_10_trips/top.age60plus_mean_weekday_07_10_trips.where(top.age60plus_mean_weekday_07_10_trips.gt(0))
top=top.sort_values('all_age_mean_weekday_07_10_trips',ascending=False).head(10)
assert len(top)==10 and top.all_age_mean_weekday_07_10_trips.ge(top.age60plus_mean_weekday_07_10_trips-1e-5).all()
top.to_csv(OUT/'general_population_top10_OD_NOT_DRT_DEMAND.csv',index=False)

# q is completed passenger journeys / ALL covered vehicle hours, not on-board occupancy.
central=list(csv.DictReader((ROOT/'outputs/tables/seoul_cost_verification/central_case.csv').open()))[0]
annual=float(central['annual_recurring_assumption_krw']);hours=5*365
assert annual==145000000
cost=[]
for cost_multiplier,q in itertools.product([1,1.2],[.9,1,1.5,2.1,3,3.9]):
    cost.append({'assumed_completed_journeys_per_covered_vehicle_hour':q,
        'cost_multiplier':cost_multiplier,'annual_cost_assumption_krw':annual*cost_multiplier,'annual_covered_vehicle_hours':hours,
        'conditional_annual_completed_journeys':q*hours,'conditional_cost_per_journey_krw':annual*cost_multiplier/(q*hours),
        'status':'illustrative budget; UK q stress range not a Seoul forecast; recurring cost excludes purchase/setup'})
pd.DataFrame(cost).to_csv(OUT/'conditional_unit_cost.csv',index=False)
thresholds={'hourly_cost_from_previous_plan_krw':annual/hours,
 'q_to_match_historical_calltaxi_59700':annual/hours/59700,
 'q_to_match_historical_corporate_accessible_44025':annual/hours/44025,
 'comparison_limit':'Historical average costs are not current marginal costs or like-for-like service quotes'}
(OUT/'cost_thresholds.json').write_text(json.dumps(thresholds,ensure_ascii=False,indent=2))

# P = direct passenger-km of the new DRT service. Existing transit supply stays fixed.
# p is the share of P that replaces car PERSON-km, m is prior car occupancy.
# n is passenger-km / loaded DRT vehicle-km, including detours; never q above.
# Thus loaded DRT km = P*(1+d)/n, and avoided car vehicle-km=P*p/m.
def vkt(p,n,e,d,m=1):
    if not all(math.isfinite(x) for x in [p,n,e,d,m]) or not(0<=p<=1 and n>0 and e>=0 and d>=0 and m>=1):
        raise ValueError('Invalid share, occupancy or distance ratio')
    added=(1+d)*(1+e)/n
    avoided=p/m
    return added,avoided,added-avoided,m*added
assert vkt(1,1,0,0)==(1,1,0,1)
assert vkt(1,2,0,0)==(.5,1,-.5,.5)
assert math.isclose(vkt(.7,3,.77,.1)[3],.649)
for bad in [(-.1,2,0,0),(1,0,0,0),(float('nan'),2,0,0)]:
    try:vkt(*bad)
    except ValueError:pass
    else:raise AssertionError('Invalid input accepted')
grid=[]
for n,e,d,m,p in itertools.product([1,2,3,4],[.25,.45,.77,1.09],[0,.1,.2],[1,1.3],[.3,.5,.7]):
    added,avoided,change,boundary=vkt(p,n,e,d,m)
    grid.append({'assumed_loaded_distance_weighted_occupancy':n,'empty_to_loaded_distance_ratio':e,
      'detour_ratio':d,'prior_car_occupancy':m,'car_substitution_person_distance_share':p,
      'added_DRT_vehicle_km_per_1000_direct_passenger_km':1000*added,
      'avoided_car_vehicle_km_per_1000_direct_passenger_km':1000*avoided,
      'net_added_vehicle_km_negative_is_reduction':1000*change,
      'minimum_car_person_distance_share_for_strict_vkt_reduction':boundary,
      'strict_reduction':change<0,'status':'conditional accounting, not network congestion or causal impact'})
assert len(grid)==288
pd.DataFrame(grid).to_csv(OUT/'vehicle_km_sensitivity_NOT_CONGESTION_IMPACT.csv',index=False)
metadata={'raw_rows':raw_rows,'service_records':len(data),'treatment_records':int(data.treatment.sum()),
 'general_population_input':'Existing 84-day 2026 Jul6-Sep27 official telecom aggregates; 56 regular weekdays; morning departures to different Seoul dong. No mode, facility, individual scheduling or adoption observed.',
 'general_population_source_sha256':telecom_source_hash,
 'packaged_telecom_input_sha256':hashlib.file_digest(compact.open('rb'),'sha256').hexdigest(),
 'UK_source_url':'https://assets.publishing.service.gov.uk/media/69383a8a5cc812f50aa41e71/rmf-phase1-evaluation.pdf',
 'UK_report_sha256':hashlib.file_digest((ROOT/'data/raw/drt_cost_evidence/uk_rmf_phase1_evaluation_2025.pdf').open('rb'),'sha256').hexdigest(),
 'UK_evidence':'18 rural/suburban schemes; latest monitoring Apr-Sep2024; report published Dec2025; q range0.9-3.9 mean2.1, empty/loaded range0.45-1.09 mean0.77, section5.5 printedp37',
 'assumptions':'n=1-4 and d=0-20%, p=30-70%, prior car occupancy1 or1.3 are uncalibrated sensitivity values. UK empty/q cannot be directly transferred to Seoul.',
 'baseline':'NEW general-use DRT vs prior travel; no existing bus/taxi service withdrawal or avoided original accessible taxi km assumed; not primary-cohort service replacement.',
 'actual_adoption':None,'actual_car_shift':None,'actual_unit_cost':None,'actual_congestion_effect':None,
 'conclusion':'Broader service cohort has more co-occurrence, but public take-up/cost/VKT benefits not established; validate restricted-corridor integration while preserving support.'}
(OUT/'verification_scope.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
print(coocc[(coocc.minutes==30)&(coocc.bin_offset_minutes==0)].to_string(index=False))
print(top.to_string(index=False))
print(pd.DataFrame(cost).round(2).to_string(index=False))
print(thresholds)
