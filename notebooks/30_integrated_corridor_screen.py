"""Link telecom flows, sampled bus routes/headways, centroid access and repeatability.

A descriptive alternative-screen, not verified transport deprivation or DRT demand.
All code/name joins are exact normalized-label scenarios, not boundary equivalence.
"""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables/integrated_corridor_screen';OUT.mkdir(parents=True,exist_ok=True)
RAW=ROOT/'data/raw';FLOW=ROOT/'outputs/tables/telecom_12weeks'
DISTRICTS='종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구'.split()
def normalize(s):return s.str.replace('·','',regex=False).str.replace('.','',regex=False).str.replace(' ','',regex=False)
def distance(lat,lon,lat2,lon2):
    a=np.sin(np.radians(lat2-lat)/2)**2+np.cos(np.radians(lat))*np.cos(np.radians(lat2))*np.sin(np.radians(lon2-lon)/2)**2
    return 6371000*2*np.arcsin(np.sqrt(np.clip(a,0,1)))
assert abs(float(distance(37,127,np.array([37]),np.array([127]))[0]))<1e-9
centroids=[];heads=[];walks=[];input_paths=[]
for i,district in enumerate(DISTRICTS,1):
    code=str(11000+i*10)
    for name,collection in [('dong_centroids',centroids),('headway',heads),('dong_walk_input',walks)]:
        p=RAW/f'{name}_{code}.csv';input_paths.append(p)
        f=pd.read_csv(p,dtype={'dong_code':str,'stop_id':str,'route_id':str})
        f['district']=district;collection.append(f)
centroid=pd.concat(centroids,ignore_index=True)
walk=pd.concat(walks,ignore_index=True)
head=pd.concat(heads,ignore_index=True).drop_duplicates(['stop_id','route_id'])
assert not centroid.dong_code.duplicated().any() and not walk.dong_code.duplicated().any()
head['headway_min']=pd.to_numeric(head.headway_min,errors='coerce')
head=head[head.headway_min.gt(0)]
with zipfile.ZipFile(RAW/'telecom/admdong_codes.zip') as z:
    official=pd.read_csv(z.open('SEOUL_ADMI/ADMI_202608.csv'),dtype=str)
official=official[official.SIDO_NM.eq('서울특별시')].copy()
official['lookup']=normalize(official.ADMI_NM);centroid['lookup']=normalize(centroid.dong_name)
assert not official.duplicated(['SGG_NM','lookup']).any() and not centroid.duplicated(['district','lookup']).any()
nodes=official.merge(centroid,left_on=['SGG_NM','lookup'],right_on=['district','lookup'],how='left',validate='one_to_one',indicator=True)
coverage={'official_seoul_dongs':len(nodes),'centroid_exact_name_matches':int(nodes._merge.eq('both').sum()),
          'unmatched_names':nodes.loc[nodes._merge.ne('both'),'FULL_NM'].tolist()}
nodes=nodes.drop(columns='_merge').merge(walk[['dong_code','stop_id','distance_m','slope']],on='dong_code',how='left',validate='many_to_one')
terms=head.groupby('stop_id').headway_min.agg(nearest_fastest_headway_min='min',nearest_mean_headway_min='mean',nearest_observed_route_count='size').reset_index()
nodes=nodes.merge(terms,on='stop_id',how='left',validate='many_to_one')
route_sets=head.groupby('stop_id').route_id.agg(set).to_dict()
stops=pd.read_csv(RAW/'bus_stops_seoul.csv',dtype={'stop_id':str})
assert not stops.stop_id.duplicated().any() and stops.lat.notna().all() and stops.lon.notna().all()
known=head.groupby('stop_id').headway_min.min().rename('fastest').reset_index().merge(stops[['stop_id','lat','lon']],on='stop_id',how='inner',validate='one_to_one')
coverage['sampled_headway_stops']=int(head.stop_id.nunique());coverage['sampled_stops_with_coordinates']=len(known)
for idx,row in nodes[nodes.lat.notna()].iterrows():
    all_d=distance(row.lat,row.lon,stops.lat.to_numpy(),stops.lon.to_numpy())
    sampled_d=distance(row.lat,row.lon,known.lat.to_numpy(),known.lon.to_numpy())
    for radius in [300,500]:
        selected=known.loc[sampled_d<=radius]
        nodes.loc[idx,f'all_bus_stops_{radius}m']=int((all_d<=radius).sum())
        nodes.loc[idx,f'sampled_headway_stops_{radius}m']=len(selected)
        nodes.loc[idx,f'sampled_nearby_fastest_{radius}m_min']=selected.fastest.min()
    expected=float(all_d.min())
    # Distance disagreement remains visible, never silently corrected across source snapshots.
    nodes.loc[idx,'recomputed_nearest_distance_m']=expected
nodes['centroid_walk_proxy_min_1p2mps']=nodes.distance_m*(1+.5*nodes.slope)/72
nodes['centroid_walk_proxy_min_0p8mps']=nodes.distance_m*(1+.5*nodes.slope)/48
nodes.to_csv(OUT/'seoul_nodes_and_bus_coverage.csv',index=False)
pilot=nodes[nodes.SGG_NM.isin(['중구','성동구','동대문구'])].copy()
assert len(pilot)==47 and pilot.dong_code.notna().sum()==45

hour_source=FLOW/'outbound_od_hour_mean_trips.csv';hour_compact=OUT/'hourly_flow_INPUT_weekday_6hours.csv'
if hour_source.exists():
    parts=[]
    for c in pd.read_csv(hour_source,chunksize=200000,dtype={'o_admdong_cd':str,'d_admdong_cd':str}):
        keep=c.day_type.eq('weekday')&c.hour.isin([7,8,9,17,18,19])&c.o_admdong_cd.isin(pilot.ADMI_CD)&c.d_admdong_cd.isin(nodes.ADMI_CD)&c.o_admdong_cd.ne(c.d_admdong_cd)
        parts.append(c.loc[keep,['o_admdong_cd','d_admdong_cd','hour','total_cnt','60plus_cnt']])
    hourly=pd.concat(parts,ignore_index=True);hourly.to_csv(hour_compact,index=False)
else:
    old=json.loads((OUT/'manifest.json').read_text())
    assert hashlib.file_digest(hour_compact.open('rb'),'sha256').hexdigest()==old['hourly_compact_sha256']
    hourly=pd.read_csv(hour_compact,dtype={'o_admdong_cd':str,'d_admdong_cd':str})
assert not hourly.duplicated(['o_admdong_cd','d_admdong_cd','hour']).any()
assert hourly.total_cnt.ge(hourly['60plus_cnt']-1e-6).all()
morning=hourly[hourly.hour.between(7,9)]
corridors=morning.groupby(['o_admdong_cd','d_admdong_cd']).agg(morning_all_age_mean_trips=('total_cnt','sum'),morning_60plus_mean_trips=('60plus_cnt','sum')).reset_index()
for prefix,key in [('origin','o_admdong_cd'),('destination','d_admdong_cd')]:
    fields=['ADMI_CD','FULL_NM','SGG_NM','dong_name','lat','lon','stop_id','nearest_fastest_headway_min','nearest_mean_headway_min','centroid_walk_proxy_min_1p2mps','all_bus_stops_300m','all_bus_stops_500m','sampled_nearby_fastest_300m_min','sampled_nearby_fastest_500m_min']
    renamed=nodes[fields].rename(columns={c:f'{prefix}_{c}' for c in fields if c!='ADMI_CD'})
    corridors=corridors.merge(renamed,left_on=key,right_on='ADMI_CD',how='left',validate='many_to_one').drop(columns='ADMI_CD')
corridors['centroid_straight_line_km']=distance(corridors.origin_lat.to_numpy(),corridors.origin_lon.to_numpy(),corridors.destination_lat.to_numpy(),corridors.destination_lon.to_numpy())/1000
shared=[];shared_min=[]
for row in corridors.itertuples():
    a=route_sets.get(row.origin_stop_id);b=route_sets.get(row.destination_stop_id)
    common=a&b if a is not None and b is not None else None
    shared.append(len(common) if common is not None else np.nan)
    # This says a common route ID exists, not verified stop order or travel time.
    shared_min.append(min([float(head.loc[head.route_id.eq(r),'headway_min'].min()) for r in common],default=np.nan) if common is not None else np.nan)
corridors['common_sampled_route_count']=shared;corridors['common_route_fastest_recorded_headway_min']=shared_min
pair_keys=['o_admdong_cd','d_admdong_cd']
lookup=hourly.set_index(pair_keys+['hour']).total_cnt.to_dict()
reverse=[];balanced=[]
for row in corridors.itertuples():
    if row.d_admdong_cd not in set(pilot.ADMI_CD):reverse.append(np.nan);balanced.append(np.nan);continue
    vals=[lookup.get((row.d_admdong_cd,row.o_admdong_cd,h)) for h in [7,8,9]]
    if any(v is None for v in vals):reverse.append(np.nan);balanced.append(np.nan);continue
    f=[lookup.get((row.o_admdong_cd,row.d_admdong_cd,h),0) for h in [7,8,9]]
    reverse.append(sum(vals));balanced.append(2*sum(min(a,b) for a,b in zip(f,vals))/(sum(f)+sum(vals)))
corridors['reverse_morning_mean_trips_if_covered']=reverse
corridors['hour_aligned_bidirectional_balance_NOT_OCCUPANCY']=balanced
corridors['common_route_evidence']=np.select([corridors.common_sampled_route_count.gt(0),corridors.common_sampled_route_count.eq(0)],['shared_route_ID_present','none_at_two_sampled_stops_NOT_no_transit'],default='missing_route_data')
corridors=corridors.sort_values('morning_all_age_mean_trips',ascending=False).reset_index(drop=True)
assert len(corridors)==len(corridors.drop_duplicates(pair_keys))

# Transparent alternative screens rather than a synthetic weighted score.
base=corridors.head(10).copy();base['screen']='largest_morning_flows'
nearest=corridors[corridors.origin_nearest_fastest_headway_min.ge(15)].head(10).copy();nearest['screen']='nearest_stop_fastest_ge15_ILLUSTRATIVE'
nearby=corridors[corridors.origin_sampled_nearby_fastest_500m_min.ge(15)].head(10).copy();nearby['screen']='sampled_500m_fastest_ge15_ILLUSTRATIVE'
shortlist=pd.concat([base,nearest,nearby],ignore_index=True)
pairs=shortlist[pair_keys].drop_duplicates();pair_set=set(map(tuple,pairs.to_numpy()))
daily_source=FLOW/'daily_outbound_od_trips.csv';daily_compact=OUT/'daily_selected_OD_INPUT_84days.csv'
if daily_source.exists():
    parts=[]
    for c in pd.read_csv(daily_source,chunksize=200000,dtype={'o_admdong_cd':str,'d_admdong_cd':str,'date':str}):
        mask=[(a,b) in pair_set for a,b in zip(c.o_admdong_cd,c.d_admdong_cd)]
        parts.append(c.loc[mask,['o_admdong_cd','d_admdong_cd','date','day_type','total_cnt']])
    daily=pd.concat(parts,ignore_index=True);daily.to_csv(daily_compact,index=False)
else:
    old=json.loads((OUT/'manifest.json').read_text())
    assert hashlib.file_digest(daily_compact.open('rb'),'sha256').hexdigest()==old['daily_compact_sha256']
    daily=pd.read_csv(daily_compact,dtype={'o_admdong_cd':str,'d_admdong_cd':str,'date':str})
calendar=pd.read_csv(FLOW/'analysis_calendar.csv',dtype={'date':str})
calendar['date']=pd.to_datetime(calendar.date).dt.strftime('%Y%m%d')
assert len(calendar)==84 and calendar.day_type.eq('weekday').sum()==56
assert not daily.duplicated(pair_keys+['date']).any()
daily['date_dt']=pd.to_datetime(daily.date,format='%Y%m%d');daily['week']=daily.date_dt.dt.to_period('W-SUN').astype(str)
repeat=[]
for a,b in pair_set:
    d=daily[daily.o_admdong_cd.eq(a)&daily.d_admdong_cd.eq(b)]
    weekday=d[d.day_type.eq('weekday')]
    old=weekday[weekday.date.between('20260907','20260920')].total_cnt.mean()
    other=weekday[~weekday.date.between('20260907','20260920')].total_cnt.mean()
    repeat.append({'o_admdong_cd':a,'d_admdong_cd':b,'all_day_published_positive_days':int(d.total_cnt.gt(0).sum()),
        'all_day_positive_week_count':d.loc[d.total_cnt.gt(0),'week'].nunique(),
        'all_day_weekday_mean_on_published_days':weekday.total_cnt.mean(),
        'original_two_week_all_day_weekday_mean':old,'other_ten_week_all_day_weekday_mean':other,
        'other_vs_original_all_day_pct':100*(other/old-1) if old>0 else np.nan,
        'weekend_all_day_mean_on_published_days':d[d.day_type.eq('weekend')].total_cnt.mean()})
repeat=pd.DataFrame(repeat)
shortlist=shortlist.merge(repeat,on=pair_keys,how='left',validate='many_to_one')
assert shortlist.all_day_positive_week_count.le(12).all() and shortlist.all_day_published_positive_days.le(84).all()
shortlist.to_csv(OUT/'shortlist_with_alternatives_and_repetition.csv',index=False)
corridors.to_csv(OUT/'all_corridors_with_transit_proxies.csv',index=False)
repeat.to_csv(OUT/'selected_corridor_ALL_DAY_repetition.csv',index=False)

sensitivity=[]
for threshold in [10,15,20,30]:
    for kind,col in [('nearest','origin_nearest_fastest_headway_min'),('sampled_300m','origin_sampled_nearby_fastest_300m_min'),('sampled_500m','origin_sampled_nearby_fastest_500m_min')]:
        part=corridors[corridors[col].ge(threshold)]
        sensitivity.append({'headway_screen_minutes':threshold,'screen':kind,'origin_dongs':part.o_admdong_cd.nunique(),
            'directed_OD_pairs':len(part),'morning_mean_flow_sum_NOT_DRT_DEMAND':part.morning_all_age_mean_trips.sum()})
pd.DataFrame(sensitivity).to_csv(OUT/'headway_threshold_sensitivity.csv',index=False)
summary={'all_directed_morning_OD_pairs':len(corridors),'total_morning_flow_NOT_DRT_DEMAND':corridors.morning_all_age_mean_trips.sum(),
 'unmatched_origin_coordinate_OD_pairs':int(corridors.origin_lat.isna().sum()),
 'unmatched_destination_coordinate_OD_pairs':int(corridors.destination_lat.isna().sum()),
 'top10_common_sampled_route_present':int(base.common_sampled_route_count.gt(0).sum()),
 'nearest_ge15_origin_names':pilot.loc[pilot.nearest_fastest_headway_min.ge(15),'FULL_NM'].tolist(),
 'nearby500_ge15_origin_names':pilot.loc[pilot.sampled_nearby_fastest_500m_min.ge(15),'FULL_NM'].tolist(),
 'shortlisted_unique_pairs':len(pair_set),'coverage':coverage,
 'scope':'84-day telecom aggregates; 56 regular weekdays, 07-09 departures to other Seoul dongs; only three origin districts. Daily repetition is ALL DAY, not daily morning validation.',
 'limits':['Label matches do not verify historical boundaries','Centroid straight-line access is not residential walking or accessible path',
 'Headways are stored route terms, not time-specific actual intervals; sampled nearest stops do not cover all nearby routes',
 'Shared route ID does not prove direction, stop sequence or door-to-door feasibility; no overlap does not prove no public transport',
 'No metro routes or wheelchair boarding suitability, mode shift, willingness or actual car reduction observed',
 'All periods previously explored; screens are descriptive, not independent model validation'],
 'decision':'Use these as alternative-comparison candidates, not confirmed gaps or selected DRT routes'}
(OUT/'assessment.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
manifest={'hourly_compact_sha256':hashlib.file_digest(hour_compact.open('rb'),'sha256').hexdigest(),
 'daily_compact_sha256':hashlib.file_digest(daily_compact.open('rb'),'sha256').hexdigest(),
 'inputs':{str(p.relative_to(ROOT)):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in input_paths+[RAW/'telecom/admdong_codes.zip',RAW/'bus_stops_seoul.csv',FLOW/'analysis_calendar.csv']},
 'full_sources':{str(p.relative_to(ROOT)):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in [hour_source,daily_source] if p.exists()},
 'compact_semantics':'Full eligible six-hour mean OD and full selected-pair daily all-day rows; packaged reproduction, not independent raw telecom verification'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
print(shortlist[['screen','origin_FULL_NM','destination_FULL_NM','morning_all_age_mean_trips','origin_nearest_fastest_headway_min','origin_sampled_nearby_fastest_500m_min','common_sampled_route_count','all_day_positive_week_count']].round(2).to_string(index=False))
