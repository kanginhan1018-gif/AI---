"""Check whether long OD candidates have a one-seat bus path in the official stop-sequence file.

This is a centroid-buffer screen; it cannot establish passenger accessibility, travel time,
transfers to rail, or absence of public transport.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/raw/bus_routes_seoul_20260902.xlsx'
BASE=ROOT/'outputs/tables/open_pooling_verification'
INTEGRATED=ROOT/'outputs/tables/integrated_corridor_screen'
OUT=BASE
NETWORK_SOURCE='https://data.seoul.go.kr/dataList/OA-1095/S/1/datasetView.do'
RADIUS_M=500

od=pd.read_csv(BASE/'pilot_morning_OD_bus_overlay.csv',dtype={'o_admdong_cd':str,'d_admdong_cd':str})
spatial=pd.read_csv(INTEGRATED/'all_corridors_with_transit_proxies.csv',dtype={'o_admdong_cd':str,'d_admdong_cd':str})
cohort=od[(od.origin_bus_connectivity_screen.eq('no representative shared route'))&od.straight_line_centroid_km.ge(5)].merge(
    spatial,on=['o_admdong_cd','d_admdong_cd'],validate='one_to_one',suffixes=('_base','_network'))
assert len(cohort)==15012 and cohort.origin_lat_network.notna().all() and cohort.destination_lat_network.notna().all()

net=pd.read_excel(DATA,dtype={'ROUTE_ID':str,'NODE_ID':str})
required={'ROUTE_ID','노선명','순번','NODE_ID','정류소명','X좌표','Y좌표'}
assert required.issubset(net.columns)
net=net.dropna(subset=['ROUTE_ID','NODE_ID','순번','X좌표','Y좌표']).copy()
net['ROUTE_ID']=net.ROUTE_ID.str.strip();net['NODE_ID']=net.NODE_ID.str.strip()
net['순번']=pd.to_numeric(net['순번'],errors='raise').astype(int)
net['X좌표']=pd.to_numeric(net['X좌표'],errors='raise');net['Y좌표']=pd.to_numeric(net['Y좌표'],errors='raise')
assert not net.duplicated(['ROUTE_ID','순번']).any()

# One consistent coordinate per stop ID, then retain every route's ordered stop rows.
nodes=net.groupby('NODE_ID',as_index=False).agg(lon=('X좌표','median'),lat=('Y좌표','median'))
node_lat=nodes.lat.to_numpy();node_lon=nodes.lon.to_numpy();node_ids=nodes.NODE_ID.to_numpy()
dong_names=set(cohort.origin_FULL_NM)|set(cohort.destination_FULL_NM)
route_stops={}
for name in dong_names:
    rows=cohort.loc[cohort.origin_FULL_NM.eq(name),['origin_lat_network','origin_lon_network']].rename(columns={'origin_lat_network':'origin_lat','origin_lon_network':'origin_lon'})
    if rows.empty: rows=cohort.loc[cohort.destination_FULL_NM.eq(name),['destination_lat_network','destination_lon_network']].rename(columns={'destination_lat_network':'origin_lat','destination_lon_network':'origin_lon'})
    lat=float(rows.iloc[0].origin_lat);lon=float(rows.iloc[0].origin_lon)
    a=np.sin(np.radians(node_lat-lat)/2)**2+np.cos(np.radians(lat))*np.cos(np.radians(node_lat))*np.sin(np.radians(node_lon-lon)/2)**2
    distance=6371000*2*np.arcsin(np.sqrt(np.clip(a,0,1)))
    near=set(node_ids[distance<=RADIUS_M])
    local=net[net.NODE_ID.isin(near)].copy()
    local['centroid_distance_m']=local.NODE_ID.map(dict(zip(nodes.NODE_ID,distance)))
    route_stops[name]={rid:g.sort_values('순번')[['순번','NODE_ID','정류소명','centroid_distance_m']].to_dict('records')
                       for rid,g in local.groupby('ROUTE_ID',sort=False)}

rows=[];direct_evidence=[]
for r in cohort.itertuples():
    origin_routes=route_stops[r.origin_FULL_NM];destination_routes=route_stops[r.destination_FULL_NM]
    candidates=[]
    for rid in origin_routes.keys() & destination_routes.keys():
        b=max(destination_routes[rid],key=lambda x:x['순번'])
        before=[a for a in origin_routes[rid] if a['순번']<b['순번']]
        if before:
            a=min(before,key=lambda x:x['centroid_distance_m'])
            name=str(net.loc[net.ROUTE_ID.eq(rid),'노선명'].iloc[0])
            candidates.append((a['centroid_distance_m']+b['centroid_distance_m'],b['순번']-a['순번'],rid,name,a,b))
    candidates.sort(key=lambda x:(x[0],x[1],x[2]))
    rows.append({'o_admdong_cd':r.o_admdong_cd,'d_admdong_cd':r.d_admdong_cd,
        'origin_name':r.origin_name,'destination_name':r.destination_name,
        'mean_weekday_07_10_all_age':r.mean_weekday_07_10_all_age,
        'mean_weekday_07_10_60plus':r.mean_weekday_07_10_60plus,
        'centroid_straight_line_km':r.straight_line_centroid_km,
        'origin_radius_stop_count':len({s['NODE_ID'] for rr in origin_routes.values() for s in rr}),
        'destination_radius_stop_count':len({s['NODE_ID'] for rr in destination_routes.values() for s in rr}),
        'origin_route_count_in_radius':len(origin_routes),'destination_route_count_in_radius':len(destination_routes),
        'direct_bus_route_found_within_500m':bool(candidates),
        'direct_bus_route_count_within_500m':len({x[2] for x in candidates}),
        'direct_route_ids':'|'.join(dict.fromkeys(x[2] for x in candidates)),
        'direct_route_names':'|'.join(dict.fromkeys(x[3] for x in candidates)),
        'screen':'September 2 route-stop sequence; centroid 500m stop buffers; origin sequence < destination sequence'})
    for _,_,rid,name,a,b in candidates:
        direct_evidence.append({'origin_name':r.origin_name,'destination_name':r.destination_name,
            'route_id':rid,'route_name':name,'board_stop':a['정류소명'],'board_sequence':a['순번'],
            'board_centroid_distance_m':a['centroid_distance_m'],'alight_stop':b['정류소명'],
            'alight_sequence':b['순번'],'alight_centroid_distance_m':b['centroid_distance_m'],
            'mean_weekday_07_10_all_age':r.mean_weekday_07_10_all_age})

result=pd.DataFrame(rows)
assert len(result)==15012 and not result.duplicated(['o_admdong_cd','d_admdong_cd']).any()
assert result.direct_bus_route_found_within_500m.sum()==3431
jeonnong=result[result.origin_name.eq('서울특별시 동대문구 전농1동')&result.destination_name.eq('서울특별시 종로구 종로1.2.3.4가동')].iloc[0]
imun=result[result.origin_name.eq('서울특별시 동대문구 이문1동')&result.destination_name.eq('서울특별시 종로구 종로1.2.3.4가동')].iloc[0]
assert jeonnong.direct_route_names=='272' and not imun.direct_bus_route_found_within_500m
result.to_csv(OUT/'pilot_long_OD_route_sequence_check.csv',index=False)
pd.DataFrame(direct_evidence).to_csv(OUT/'pilot_long_OD_direct_bus_route_evidence.csv',index=False)
evidence=pd.DataFrame(direct_evidence)
route272=evidence[evidence.origin_name.eq('서울특별시 동대문구 전농1동')&evidence.destination_name.eq('서울특별시 종로구 종로1.2.3.4가동')&evidence.route_name.eq('272')].iloc[0]
assert route272.board_sequence==16 and route272.alight_sequence==64
summary={'source_file':'data/raw/bus_routes_seoul_20260902.xlsx','source_url':NETWORK_SOURCE,
    'file_sha256':hashlib.file_digest(DATA.open('rb'),'sha256').hexdigest(),
    'file_date':'2026-09-02','OD_period':'2026-07-06 to 2026-09-27; 56 regular weekdays; 07-09 hourly mean flows summed',
    'network_route_stop_rows':len(net),'network_routes':int(net.ROUTE_ID.nunique()),'network_unique_stops':len(nodes),
    'candidate_OD_pairs':len(result),'direct_bus_route_pairs':int(result.direct_bus_route_found_within_500m.sum()),
    'direct_bus_route_pairs_pct':100*result.direct_bus_route_found_within_500m.mean(),
    'direct_route_mean_weekday_flow':float(result.loc[result.direct_bus_route_found_within_500m,'mean_weekday_07_10_all_age'].sum()),
    'candidate_mean_weekday_flow':float(result.mean_weekday_07_10_all_age.sum()),
    'no_direct_bus_in_buffer_pairs':int((~result.direct_bus_route_found_within_500m).sum()),
    'no_direct_bus_in_buffer_flow':float(result.loc[~result.direct_bus_route_found_within_500m,'mean_weekday_07_10_all_age'].sum()),
    'method':'For each OD, any September route ID with a listed origin-buffer stop preceding a destination-buffer stop by sequence number is a direct-bus path candidate.',
    'radius_m':RADIUS_M,'limits':['Administrative-dong centroid buffers are not passenger origins/destinations or accessible walking paths.',
    'One-seat bus sequence does not include waiting, in-vehicle time, fare, real-time operation, rail or transfers.',
    'No route found in these two buffers does not mean no public-transport path; stops beyond 500m and transfers/rail are untested.',
    'Route file snapshot predates end of telecom period by 25 days.']}
(OUT/'route_sequence_check_scope.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
