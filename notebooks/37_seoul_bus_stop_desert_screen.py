"""Citywide screen for Seoul administrative-dong centroids with sparse bus-stop access.

This joins bus stop points and a derived rail station coordinate master at dong centroids.
It is a straight-line access screen, not pedestrian-network or person-level accessibility.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / 'outputs/tables/integrated_corridor_screen/seoul_nodes_and_bus_coverage.csv'
STOPS = ROOT / 'data/raw/bus_stops_seoul.csv'
HEAD_DIR = ROOT / 'data/raw'
OUT = ROOT / 'outputs/tables/non_drt_policy_comparison'
OUT.mkdir(parents=True, exist_ok=True)
STATIONS = ROOT / 'data/raw/subway_station_coords_derived_20260630.csv'

def haversine_m(lat, lon, lats, lons):
    a = np.sin(np.radians(lats-lat)/2)**2 + np.cos(np.radians(lat))*np.cos(np.radians(lats))*np.sin(np.radians(lons-lon)/2)**2
    return 6371000 * 2*np.arcsin(np.sqrt(np.clip(a, 0, 1)))

nodes = pd.read_csv(NODES, dtype={'ADMI_CD': str, 'dong_code': str, 'stop_id': str})
stops = pd.read_csv(STOPS, dtype={'stop_id': str})
stops = stops[~stops.stop_name.astype(str).str.contains('한강버스', na=False)].drop_duplicates('stop_id').copy()
stations = pd.read_csv(STATIONS, encoding='utf-8-sig')
heads = pd.concat([pd.read_csv(p, dtype={'stop_id': str, 'route_id': str}) for p in HEAD_DIR.glob('headway_*.csv')], ignore_index=True)
heads['headway_min'] = pd.to_numeric(heads.headway_min, errors='coerce')
heads = heads[heads.headway_min.gt(0)]
stop_head = heads.groupby('stop_id').agg(sampled_route_count=('route_id','nunique'),
    fastest_recorded_route_term_min=('headway_min','min'), mean_recorded_route_term_min=('headway_min','mean')).reset_index()
stops = stops.merge(stop_head, on='stop_id', how='left', validate='one_to_one')

rows=[]
for r in nodes.itertuples():
    dist=haversine_m(float(r.lat),float(r.lon),stops.lat.to_numpy(),stops.lon.to_numpy())
    nearest=int(np.argmin(dist));s=stops.iloc[nearest]
    row={'ADMI_CD':r.ADMI_CD,'FULL_NM':r.FULL_NM,'lat':r.lat,'lon':r.lon,
         'nearest_bus_stop_id':s.stop_id,'nearest_bus_stop_name':s.stop_name,
         'nearest_bus_stop_ars_id':s.ars_id,'nearest_bus_stop_straight_line_m':float(dist[nearest]),
         'bus_stops_within_300m':int((dist<=300).sum()),'bus_stops_within_500m':int((dist<=500).sum()),
         'bus_stops_within_800m':int((dist<=800).sum()),
         'nearest_stop_sampled_route_count':s.sampled_route_count,
         'nearest_stop_fastest_recorded_route_term_min':s.fastest_recorded_route_term_min,
         'nearest_stop_mean_recorded_route_term_min':s.mean_recorded_route_term_min,
         'centroid_slope_proxy':r.slope,
         'centroid_walk_time_proxy_min_at_1p2mps_slope_adjusted':r.centroid_walk_proxy_min_1p2mps}
    sd=haversine_m(float(r.lat),float(r.lon),stations.lat.to_numpy(),stations.lng.to_numpy())
    si=int(np.argmin(sd)); metro=stations.iloc[si]
    row.update({'nearest_rail_station_name':metro.station,'nearest_rail_station_lines':metro.lines,
                'nearest_rail_station_straight_line_m':float(sd[si])})
    rows.append(row)
res=pd.DataFrame(rows)
res['bus_access_priority_screen']=np.select(
    [res.nearest_bus_stop_straight_line_m.ge(800)&res.bus_stops_within_500m.eq(0),
     res.nearest_bus_stop_straight_line_m.ge(500)&res.bus_stops_within_500m.eq(0)],
    ['high_bus_access_screen','moderate_bus_access_screen'],default='no_centroid_bus_access_flag')
# Provisional screening convention, not an official Seoul service standard.
res['dual_bus_rail_access_screen']=np.select(
    [res.nearest_bus_stop_straight_line_m.ge(800)&res.nearest_rail_station_straight_line_m.ge(1000),
     res.nearest_bus_stop_straight_line_m.ge(500)&res.nearest_rail_station_straight_line_m.ge(800)],
    ['high_dual_access_screen','moderate_dual_access_screen'],default='no_dual_access_flag')
res=res.sort_values(['nearest_bus_stop_straight_line_m','bus_stops_within_500m'],ascending=[False,True])
res.to_csv(OUT/'seoul_dong_bus_stop_sparse_screen.csv',index=False)
summary=res.groupby('bus_access_priority_screen',as_index=False).agg(
    administrative_dongs=('ADMI_CD','size'),
    median_nearest_stop_m=('nearest_bus_stop_straight_line_m','median'),
    median_bus_stops_500m=('bus_stops_within_500m','median'),
    median_nearest_stop_fastest_term_min=('nearest_stop_fastest_recorded_route_term_min','median'))
summary.to_csv(OUT/'seoul_dong_bus_stop_sparse_summary.csv',index=False)
print('dongs',len(res),'unique',res.ADMI_CD.nunique())
print('dual access counts',res.dual_bus_rail_access_screen.value_counts().to_dict())
print(summary.to_string(index=False))
print('\nTop candidates:')
print(res.head(20)[['FULL_NM','nearest_bus_stop_name','nearest_bus_stop_straight_line_m','bus_stops_within_500m','nearest_rail_station_name','nearest_rail_station_straight_line_m','nearest_stop_fastest_recorded_route_term_min','centroid_slope_proxy']].round(1).to_string(index=False))
