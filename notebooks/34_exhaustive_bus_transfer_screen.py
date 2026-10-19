"""Exhaustively screen 0/1-transfer bus paths for the 15,012 long-OD pairs.

Uses the official 2026-09-02 ordered bus stop file and 500m administrative-dong
centroid stop buffers. It is a network connectivity screen, not a journey planner.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/raw/bus_routes_seoul_20260902.xlsx'
BASE = ROOT / 'outputs/tables/open_pooling_verification'
INTEGRATED = ROOT / 'outputs/tables/integrated_corridor_screen'
OUT = ROOT / 'outputs/tables/non_drt_policy_comparison'
OUT.mkdir(parents=True, exist_ok=True)
RADIUS_M = 500

od = pd.read_csv(BASE / 'pilot_morning_OD_bus_overlay.csv', dtype={'o_admdong_cd': str, 'd_admdong_cd': str})
spatial = pd.read_csv(INTEGRATED / 'all_corridors_with_transit_proxies.csv', dtype={'o_admdong_cd': str, 'd_admdong_cd': str})
cohort = od[(od.origin_bus_connectivity_screen.eq('no representative shared route')) & od.straight_line_centroid_km.ge(5)].merge(
    spatial, on=['o_admdong_cd', 'd_admdong_cd'], validate='one_to_one', suffixes=('_base', '_network'))
assert len(cohort) == 15012

net = pd.read_excel(DATA, dtype={'ROUTE_ID': str, 'NODE_ID': str})
required = {'ROUTE_ID', '노선명', '순번', 'NODE_ID', '정류소명', 'X좌표', 'Y좌표'}
assert required.issubset(net.columns)
net = net.dropna(subset=['ROUTE_ID', 'NODE_ID', '순번', 'X좌표', 'Y좌표']).copy()
off_hour_mask = net['노선명'].astype(str).str.match(r'^(N\d|심야|새벽)', case=False) | net['노선명'].astype(str).str.contains(r'한강|청와대A01', regex=True)
excluded_off_hour_routes = sorted(net.loc[off_hour_mask, '노선명'].astype(str).unique())
excluded_off_hour_route_count = int(net.loc[off_hour_mask, 'ROUTE_ID'].nunique())
net = net.loc[~off_hour_mask].copy()
net['ROUTE_ID'] = net.ROUTE_ID.str.strip()
net['NODE_ID'] = net.NODE_ID.str.strip()
net['순번'] = pd.to_numeric(net['순번'], errors='raise').astype(int)
net['X좌표'] = pd.to_numeric(net['X좌표'], errors='raise')
net['Y좌표'] = pd.to_numeric(net['Y좌표'], errors='raise')
assert not net.duplicated(['ROUTE_ID', '순번']).any()
# Some circular routes may list a stop more than once. Preserve every sequence
# occurrence so forward reachability can use the valid occurrence.

# For every directed route pair, index shared physical transfer stops in sequence order.
route_node = net[['ROUTE_ID', 'NODE_ID', '순번', '정류소명', '노선명']]
route_names = net.groupby('ROUTE_ID')['노선명'].first().astype(str).to_dict()
node_routes = route_node.groupby('NODE_ID', sort=False)
transfer_entries = {}
for node_id, group in node_routes:
    rows = list(group.itertuples(index=False, name=None))
    # tuple order: ROUTE_ID, NODE_ID, 순번, 정류소명, 노선명
    for a in rows:
        for b in rows:
            if a[0] == b[0]:
                continue
            transfer_entries.setdefault((a[0], b[0]), []).append((int(a[2]), int(b[2]), node_id, str(a[3]), str(b[3])))

# Keep full entries for explainable best transfer and compact arrays for fast screening.
transfer_index = {}
for key, entries in transfer_entries.items():
    entries.sort(key=lambda z: (z[0], z[1], z[2]))
    transfer_index[key] = entries

nodes = net.groupby('NODE_ID', as_index=False).agg(lon=('X좌표', 'median'), lat=('Y좌표', 'median'))
node_lat = nodes.lat.to_numpy(); node_lon = nodes.lon.to_numpy(); node_ids = nodes.NODE_ID.to_numpy()
dong_buffers = {}
names = set(cohort.origin_FULL_NM) | set(cohort.destination_FULL_NM)
for name in names:
    m = cohort.loc[cohort.origin_FULL_NM.eq(name), ['origin_lat_network', 'origin_lon_network']]
    if m.empty:
        m = cohort.loc[cohort.destination_FULL_NM.eq(name), ['destination_lat_network', 'destination_lon_network']].rename(
            columns={'destination_lat_network': 'origin_lat_network', 'destination_lon_network': 'origin_lon_network'})
    lat, lon = map(float, m.iloc[0])
    a = np.sin(np.radians(node_lat-lat)/2)**2 + np.cos(np.radians(lat))*np.cos(np.radians(node_lat))*np.sin(np.radians(node_lon-lon)/2)**2
    dist = 6371000*2*np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    nearest = pd.DataFrame({'NODE_ID': node_ids[dist <= RADIUS_M], 'distance_m': dist[dist <= RADIUS_M]})
    local = route_node[route_node.NODE_ID.isin(set(nearest.NODE_ID))].merge(nearest, on='NODE_ID', validate='many_to_one')
    # Lowest stop sequence is the most permissive boarding point; highest is the most permissive alighting point.
    dong_buffers[name] = {
        'board': local.groupby('ROUTE_ID')['순번'].min().astype(int).to_dict(),
        'alight': local.groupby('ROUTE_ID')['순번'].max().astype(int).to_dict(),
        'node_count': int(nearest.NODE_ID.nunique()),
        'routes': local.groupby('ROUTE_ID').size().index.tolist(),
        'by_route': {route: group.sort_values('순번').to_dict('records') for route, group in local.groupby('ROUTE_ID', sort=False)}
    }

rows = []
for r in cohort.itertuples():
    o = dong_buffers[r.origin_FULL_NM]
    d = dong_buffers[r.destination_FULL_NM]
    direct_routes = []
    for route in set(o['board']) & set(d['alight']):
        if o['board'][route] < d['alight'][route]:
            direct_routes.append(route)
    transfer_candidates = []
    if not direct_routes:
        for ra, board_seq in o['board'].items():
            for rb, alight_seq in d['alight'].items():
                if ra == rb:
                    continue
                entries = transfer_index.get((ra, rb), ())
                for e in entries:
                    if not (board_seq < e[0] and e[1] < alight_seq):
                        continue
                    boards = [s for s in o['by_route'][ra] if int(s['순번']) < e[0]]
                    alights = [s for s in d['by_route'][rb] if int(s['순번']) > e[1]]
                    if not boards or not alights:
                        continue
                    # Minimize listed sequence steps, then walk-to-stop distance;
                    # neither is an estimate of passenger journey time.
                    board = max(boards, key=lambda s: (int(s['순번']), -float(s['distance_m'])))
                    alight = min(alights, key=lambda s: (int(s['순번']), float(s['distance_m'])))
                    steps = int(e[0])-int(board['순번']) + int(alight['순번'])-int(e[1])
                    transfer_candidates.append((steps, ra, rb, e, board, alight))
    transfer_candidates.sort(key=lambda z: (z[0], z[1], z[2], z[3][2]))
    best = transfer_candidates[0] if transfer_candidates else None
    rows.append({
        'o_admdong_cd': r.o_admdong_cd, 'd_admdong_cd': r.d_admdong_cd,
        'origin_name': r.origin_name, 'destination_name': r.destination_name,
        'mean_weekday_07_10_all_age': r.mean_weekday_07_10_all_age,
        'mean_weekday_07_10_60plus': r.mean_weekday_07_10_60plus,
        'centroid_straight_line_km': r.straight_line_centroid_km,
        'origin_sampled_fastest_headway_500m_min': r.origin_sampled_nearby_fastest_500m_min,
        'origin_nearest_fastest_headway_min': r.origin_nearest_fastest_headway_min,
        'origin_bus_stops_500m_all_routes': r.origin_all_bus_stops_500m,
        'origin_centroid_walk_proxy_min': r.origin_centroid_walk_proxy_min_1p2mps,
        'origin_stops_500m': o['node_count'], 'destination_stops_500m': d['node_count'],
        'direct_bus_path_found': bool(direct_routes), 'direct_bus_route_count': len(direct_routes),
        'direct_bus_route_ids': '|'.join(sorted(direct_routes)),
        'direct_bus_route_names': '|'.join(sorted({route_names[x] for x in direct_routes})),
        'one_transfer_bus_path_found': bool(best), 'one_transfer_route_pair_count': len(transfer_candidates),
        'best_transfer_route_a': best[1] if best else '',
        'best_transfer_route_a_name': route_names[best[1]] if best else '',
        'best_transfer_route_b': best[2] if best else '',
        'best_transfer_route_b_name': route_names[best[2]] if best else '',
        'best_transfer_node_id': best[3][2] if best else '',
        'best_transfer_stop_name': best[3][3] if best else '',
        'best_transfer_stop_sequence_a': best[3][0] if best else np.nan,
        'best_transfer_stop_sequence_b': best[3][1] if best else np.nan,
        'candidate_board_stop': best[4]['정류소명'] if best else '',
        'candidate_board_sequence': int(best[4]['순번']) if best else np.nan,
        'candidate_board_centroid_distance_m': float(best[4]['distance_m']) if best else np.nan,
        'candidate_alight_stop': best[5]['정류소명'] if best else '',
        'candidate_alight_sequence': int(best[5]['순번']) if best else np.nan,
        'candidate_alight_centroid_distance_m': float(best[5]['distance_m']) if best else np.nan,
        'best_total_sequence_steps_NOT_TRAVEL_TIME': best[0] if best else np.nan,
        'path_class': 'direct_bus_candidate' if direct_routes else ('one_transfer_bus_candidate' if best else 'no_0_or_1_transfer_bus_path_in_screen'),
    })

result = pd.DataFrame(rows)
result['sampled_headway_ge15min'] = result.origin_sampled_fastest_headway_500m_min.ge(15)
result['service_gap_priority_screen'] = np.select(
    [result.path_class.eq('no_0_or_1_transfer_bus_path_in_screen'), result.sampled_headway_ge15min],
    ['no_direct_or_one_transfer_bus_candidate', 'nearby_sampled_fastest_headway_ge15min'],
    default='bus_path_candidate_and_sampled_headway_under15min')
assert len(result) == 15012
assert not result.duplicated(['o_admdong_cd', 'd_admdong_cd']).any()
old = pd.read_csv(BASE / 'pilot_long_OD_route_sequence_check.csv', dtype={'o_admdong_cd': str, 'd_admdong_cd': str})
check = result.merge(old[['o_admdong_cd', 'd_admdong_cd', 'direct_bus_route_found_within_500m']], on=['o_admdong_cd', 'd_admdong_cd'], validate='one_to_one')
assert not (check.direct_bus_path_found & ~check.direct_bus_route_found_within_500m).any()
off_hour_only_direct_pairs = int((check.direct_bus_route_found_within_500m & ~check.direct_bus_path_found).sum())
result.to_csv(OUT / 'all_15012_OD_bus_0_1_transfer_screen.csv', index=False)

summary = result.groupby('path_class', as_index=False).agg(
    OD_pairs=('o_admdong_cd', 'size'),
    weekday_07_09_mean_flow_sum=('mean_weekday_07_10_all_age', 'sum'),
    weekday_07_09_60plus_mean_flow_sum=('mean_weekday_07_10_60plus', 'sum'))
summary['OD_pair_share_pct'] = 100*summary.OD_pairs/len(result)
summary['flow_share_pct'] = 100*summary.weekday_07_09_mean_flow_sum/result.mean_weekday_07_10_all_age.sum()
summary.to_csv(OUT / 'all_15012_OD_bus_path_class_summary.csv', index=False)

gap_summary = result.groupby('service_gap_priority_screen', as_index=False).agg(
    OD_pairs=('o_admdong_cd', 'size'),
    weekday_07_09_mean_flow_sum=('mean_weekday_07_10_all_age', 'sum'),
    weekday_07_09_60plus_mean_flow_sum=('mean_weekday_07_10_60plus', 'sum'))
gap_summary['OD_pair_share_pct'] = 100*gap_summary.OD_pairs/len(result)
gap_summary['flow_share_pct'] = 100*gap_summary.weekday_07_09_mean_flow_sum/result.mean_weekday_07_10_all_age.sum()
gap_summary.to_csv(OUT / 'all_15012_service_gap_priority_summary.csv', index=False)

unconnected = result[result.path_class.eq('no_0_or_1_transfer_bus_path_in_screen')]
origin_gap = unconnected.groupby('origin_name', as_index=False).agg(
    OD_pairs_without_0_1_transfer_bus=('o_admdong_cd', 'size'),
    weekday_07_09_mean_flow_sum=('mean_weekday_07_10_all_age', 'sum'),
    weekday_07_09_60plus_mean_flow_sum=('mean_weekday_07_10_60plus', 'sum'),
    sampled_fastest_headway_500m_min=('origin_sampled_fastest_headway_500m_min', 'first'),
    nearest_fastest_headway_min=('origin_nearest_fastest_headway_min', 'first'),
    bus_stops_500m=('origin_bus_stops_500m_all_routes', 'first'),
    centroid_walk_proxy_min=('origin_centroid_walk_proxy_min', 'first'))
origin_gap = origin_gap.sort_values('weekday_07_09_mean_flow_sum', ascending=False)
origin_gap.to_csv(OUT / 'origin_dongs_without_0_1_transfer_bus_candidates.csv', index=False)

dest_gap = unconnected.groupby('destination_name', as_index=False).agg(
    OD_pairs_without_0_1_transfer_bus=('o_admdong_cd', 'size'),
    weekday_07_09_mean_flow_sum=('mean_weekday_07_10_all_age', 'sum'),
    weekday_07_09_60plus_mean_flow_sum=('mean_weekday_07_10_60plus', 'sum'))
dest_gap = dest_gap.sort_values('weekday_07_09_mean_flow_sum', ascending=False)
dest_gap.to_csv(OUT / 'destinations_without_0_1_transfer_bus_candidates.csv', index=False)

origin_matrix = result.groupby('origin_name', as_index=False).agg(
    all_OD_pairs=('o_admdong_cd', 'size'),
    all_weekday_07_09_mean_flow_sum=('mean_weekday_07_10_all_age', 'sum'),
    no_0_1_transfer_pairs=('path_class', lambda x: int(x.eq('no_0_or_1_transfer_bus_path_in_screen').sum())),
    no_0_1_transfer_flow=('mean_weekday_07_10_all_age', lambda x: float(x[result.loc[x.index, 'path_class'].eq('no_0_or_1_transfer_bus_path_in_screen')].sum())),
    direct_pairs=('path_class', lambda x: int(x.eq('direct_bus_candidate').sum())),
    one_transfer_pairs=('path_class', lambda x: int(x.eq('one_transfer_bus_candidate').sum())),
    headway_ge15_pairs=('sampled_headway_ge15min', 'sum'),
    headway_ge15_flow=('mean_weekday_07_10_all_age', lambda x: float(x[result.loc[x.index, 'sampled_headway_ge15min']].sum())),
    sampled_fastest_headway_500m_min=('origin_sampled_fastest_headway_500m_min', 'first'),
    bus_stops_500m=('origin_bus_stops_500m_all_routes', 'first'),
    centroid_walk_proxy_min=('origin_centroid_walk_proxy_min', 'first'))
origin_matrix = origin_matrix.sort_values(['no_0_1_transfer_flow', 'headway_ge15_flow'], ascending=False)
origin_matrix.to_csv(OUT / 'origin_dong_full_bus_gap_matrix.csv', index=False)

explain = result[result.one_transfer_bus_path_found].sort_values('mean_weekday_07_10_all_age', ascending=False).head(100)
explain.to_csv(OUT / 'top100_one_transfer_bus_candidates.csv', index=False)

meta = {
    'source_file': 'data/raw/bus_routes_seoul_20260902.xlsx',
    'source_sha256': hashlib.file_digest(DATA.open('rb'), 'sha256').hexdigest(),
    'source_snapshot': '2026-09-02',
    'excluded_off_hour_or_nonbus_routes': excluded_off_hour_routes, 'excluded_off_hour_or_nonbus_route_count': excluded_off_hour_route_count,
    'telecom_period': '2026-07-06 through 2026-09-27; 56 weekdays; sum of hourly means at 07,08,09',
    'cohort_definition': '15,012 directed OD pairs from Dongdaemun-gu, Seongdong-gu, Jung-gu; centroid straight-line distance >=5km; no common route at previous representative stops',
    'network_rows_after_night_route_exclusion': len(net), 'network_routes_after_night_route_exclusion': int(net.ROUTE_ID.nunique()), 'network_unique_stops_after_night_route_exclusion': int(net.NODE_ID.nunique()),
    'pairs_previously_flagged_direct_only_by_excluded_off_hour_or_nonbus_route': off_hour_only_direct_pairs,
    'classification_counts': summary.to_dict(orient='records'),
    'screen_priority_counts': gap_summary.to_dict(orient='records'),
    'transfer_nodes_indexed_ordered_route_pairs': sum(len(v) for v in transfer_index.values()),
    'search': 'All 500m centroid-buffer origin boarding stops and destination alighting stops, official route stop sequence; 0 or exactly 1 transfer at the same NODE_ID; each route traversed in listed sequence direction.',
    'limitations': [
        '500m from administrative-dong centroid is not a person-level or walk-network access route.',
        'Sequence connectivity is not an itinerary: no service time, waiting, transfer walk, fares, congestion, capacity, wheelchair access, or destination schedule.',
        'The file represents one listed sequence per route and does not establish both-way service unless separate route sequences support it.',
        'No path found with at most one bus transfer does not mean no transit: rail, more transfers, stops beyond 500m, and alternate route versions are omitted.',
        'Telecom flows are aggregate movements and do not reveal mode, unique persons, disability, public-service eligibility, or demand for the alternative.',
        'Route snapshot is dated 2026-09-02 while OD extends to 2026-09-27.'
    ],
    'interpretation': 'This is a complete enumeration for the defined OD cohort and static bus-network screen, not a full all-mode passenger accessibility census.'
}
(OUT / 'all_15012_OD_bus_path_scope.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
print(summary.to_string(index=False))
print(json.dumps(meta, ensure_ascii=False, indent=2))
