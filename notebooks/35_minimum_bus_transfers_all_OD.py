"""Find the minimum number of bus transfers for each of the 15,012 OD pairs.

Uses 0-1 shortest path on directed route-stop sequences: continuing along one
route costs zero transfers; changing routes at the same stop ID costs one.
This remains a static connectivity model, not a travel-time model.
"""
from pathlib import Path
from collections import deque
import json, heapq
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/raw/bus_routes_seoul_20260902.xlsx'
BASE = ROOT/'outputs/tables/open_pooling_verification'
INT = ROOT/'outputs/tables/integrated_corridor_screen'
OUT = ROOT/'outputs/tables/non_drt_policy_comparison'

od = pd.read_csv(BASE/'pilot_morning_OD_bus_overlay.csv', dtype={'o_admdong_cd':str,'d_admdong_cd':str})
spatial = pd.read_csv(INT/'all_corridors_with_transit_proxies.csv', dtype={'o_admdong_cd':str,'d_admdong_cd':str})
cohort = od[od.origin_bus_connectivity_screen.eq('no representative shared route') & od.straight_line_centroid_km.ge(5)].merge(
    spatial, on=['o_admdong_cd','d_admdong_cd'], validate='one_to_one', suffixes=('_base','_network'))
assert len(cohort)==15012

net=pd.read_excel(DATA,dtype={'ROUTE_ID':str,'NODE_ID':str})
net=net.dropna(subset=['ROUTE_ID','NODE_ID','순번','X좌표','Y좌표']).copy()
net['노선명']=net['노선명'].astype(str)
off_hour=net['노선명'].str.match(r'^(N\d|심야|새벽)',case=False) | net['노선명'].str.contains(r'한강|청와대A01',regex=True)
off_hour_route_count=int(net.loc[off_hour,'ROUTE_ID'].nunique())
net=net.loc[~off_hour].copy()
net['ROUTE_ID']=net.ROUTE_ID.str.strip();net['NODE_ID']=net.NODE_ID.str.strip()
net['순번']=pd.to_numeric(net['순번'],errors='raise').astype(int)
net=net.sort_values(['ROUTE_ID','순번']).reset_index(drop=True)
net['state_id']=np.arange(len(net),dtype=np.int32)
states=net[['state_id','ROUTE_ID','노선명','순번','NODE_ID','정류소명']]
N=len(states)
route=states.ROUTE_ID.to_numpy(); node=states.NODE_ID.to_numpy(); stop_name=states['정류소명'].astype(str).to_numpy()
route_names=states.groupby('ROUTE_ID')['노선명'].first().astype(str).to_dict()

# Directed ride edges: proceed to the next listed stop on the same route (0 added transfers).
adj=[[] for _ in range(N)]
for _,g in states.groupby('ROUTE_ID',sort=False):
    ids=g.state_id.to_numpy()
    for a,b in zip(ids[:-1],ids[1:]): adj[int(a)].append((int(b),0))

# Transfer edges: switch among route states sharing exactly the same physical stop ID (1 transfer).
for _,g in states.groupby('NODE_ID',sort=False):
    ids=g.state_id.to_numpy()
    routes=route[ids]
    for a in ids:
        for b in ids:
            if route[a]!=route[b]: adj[int(a)].append((int(b),1))

coords=net.groupby('NODE_ID',as_index=False).agg(lon=('X좌표','median'),lat=('Y좌표','median'))
node_lat=coords.lat.to_numpy();node_lon=coords.lon.to_numpy();node_ids=coords.NODE_ID.to_numpy()
buffers={}
names=set(cohort.origin_FULL_NM)|set(cohort.destination_FULL_NM)
for name in names:
    z=cohort.loc[cohort.origin_FULL_NM.eq(name),['origin_lat_network','origin_lon_network']]
    if z.empty:
        z=cohort.loc[cohort.destination_FULL_NM.eq(name),['destination_lat_network','destination_lon_network']].rename(
            columns={'destination_lat_network':'origin_lat_network','destination_lon_network':'origin_lon_network'})
    lat,lon=map(float,z.iloc[0])
    a=np.sin(np.radians(node_lat-lat)/2)**2+np.cos(np.radians(lat))*np.cos(np.radians(node_lat))*np.sin(np.radians(node_lon-lon)/2)**2
    distance=6371000*2*np.arcsin(np.sqrt(np.clip(a,0,1)))
    buffers[name]=set(node_ids[distance<=500])
buffer_states={name:states.loc[states.NODE_ID.isin(nodes),'state_id'].to_numpy(dtype=int) for name,nodes in buffers.items()}

def zero_one_search(starts):
    inf=32767
    dist=np.full(N,inf,dtype=np.int16)
    prev=np.full(N,-1,dtype=np.int32)
    dq=deque()
    for s in starts:
        dist[s]=0;dq.append(s)
    while dq:
        u=dq.popleft();du=int(dist[u])
        for v,w in adj[u]:
            nd=du+w
            if nd<dist[v]:
                dist[v]=nd;prev[v]=u
                (dq.appendleft if w==0 else dq.append)(v)
    return dist,prev

records=[]
for origin_name,g in cohort.groupby('origin_FULL_NM',sort=False):
    starts=buffer_states[origin_name].tolist()
    dist,prev=zero_one_search(starts)
    for r in g.itertuples():
        dest_states=buffer_states[r.destination_FULL_NM]
        if len(dest_states)==0:
            best=None
        else:
            j=int(np.argmin(dist[dest_states]));target=int(dest_states[j])
            best=int(dist[target]) if dist[target]<32767 else None
        if best is None:
            route_ids=[];transfer_stops=[];board='';alight=''
        else:
            chain=[];cur=target
            while cur>=0:
                chain.append(cur);cur=int(prev[cur])
            chain.reverse()
            route_ids=[];transfer_stops=[]
            for ix,s in enumerate(chain):
                if not route_ids or route[s]!=route_ids[-1]:
                    route_ids.append(route[s])
                    if ix>0: transfer_stops.append(stop_name[chain[ix-1]])
            board=stop_name[chain[0]];alight=stop_name[chain[-1]]
        records.append({
            'o_admdong_cd':r.o_admdong_cd,'d_admdong_cd':r.d_admdong_cd,
            'origin_name':r.origin_name,'destination_name':r.destination_name,
            'mean_weekday_07_10_all_age':r.mean_weekday_07_10_all_age,
            'mean_weekday_07_10_60plus':r.mean_weekday_07_10_60plus,
            'minimum_bus_transfers_in_static_graph':best,
            'minimum_bus_route_count':len(route_ids) if best is not None else 0,
            'candidate_route_ids':'|'.join(route_ids),
            'candidate_route_names':'|'.join([route_names[x] for x in route_ids]),
            'candidate_transfer_stops':'|'.join(transfer_stops),
            'candidate_board_stop':board,'candidate_alight_stop':alight,
            'screen':'one listed daytime route direction; 500m dong centroid buffers; transfer at same NODE_ID'})

result=pd.DataFrame(records)
assert len(result)==15012
assert not result.duplicated(['o_admdong_cd','d_admdong_cd']).any()
result.to_csv(OUT/'all_15012_OD_minimum_bus_transfers.csv',index=False)
result['transfer_class']=np.select(
    [result.minimum_bus_transfers_in_static_graph.eq(0),result.minimum_bus_transfers_in_static_graph.eq(1),result.minimum_bus_transfers_in_static_graph.ge(2)],
    ['0_transfer_direct_bus_candidate','1_transfer_bus_candidate','2plus_transfer_bus_candidate'],default='no_bus_path_in_static_graph')
summary=result.groupby('transfer_class',dropna=False,as_index=False).agg(
    OD_pairs=('o_admdong_cd','size'),weekday_07_09_mean_flow_sum=('mean_weekday_07_10_all_age','sum'),
    weekday_07_09_60plus_mean_flow_sum=('mean_weekday_07_10_60plus','sum'))
summary['OD_pair_share_pct']=100*summary.OD_pairs/len(result)
summary['flow_share_pct']=100*summary.weekday_07_09_mean_flow_sum/result.mean_weekday_07_10_all_age.sum()
summary.to_csv(OUT/'all_15012_OD_minimum_bus_transfers_summary.csv',index=False)

scope={
 'route_source':'data/raw/bus_routes_seoul_20260902.xlsx','route_snapshot':'2026-09-02',
 'off_hour_or_nonbus_routes_excluded':off_hour_route_count,'daytime_route_sequences':int(net.ROUTE_ID.nunique()),
 'states_route_stop_occurrences':N,'origin_dong_count':int(cohort.origin_FULL_NM.nunique()),'OD_pairs':len(result),
 'algorithm':'0-1 BFS over route-stop states: next listed stop on same route costs 0 additional transfers; changing route at same stop ID costs 1.',
 'limits':['Direction follows only the listed sequence; reverse direction is included only if separately represented.','Centroid 500m buffers are not person-level walking paths.','The graph contains no departure times, waits, travel minutes, transfer walking, fare, capacity, or accessibility.','No bus path in the graph does not establish no all-mode public transit; rail, >500m stops, and data omissions remain.','OD aggregate movements are not unique people, observed modes, or latent demand.']}
(OUT/'all_15012_OD_minimum_bus_transfers_scope.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2))
print(summary.to_string(index=False))
print(json.dumps(scope,ensure_ascii=False,indent=2))
