"""Same-cohort city comparison and retrospective temporal risk validation.

The year was previously explored: this is not an untouched or external holdout.
Prediction concerns completed-record waiting burden, not policy effects or all requests.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/tables/citywide_predictive_validation'
OUT.mkdir(parents=True, exist_ok=True)
TIMES = ['접수일시', '예정일시', '배차일시', '승차일시', '하차일시', '취소일시']
DISTRICTS = '강남구 강동구 강북구 강서구 관악구 광진구 구로구 금천구 노원구 도봉구 동대문구 동작구 마포구 서대문구 서초구 성동구 성북구 송파구 양천구 영등포구 용산구 은평구 종로구 중구 중랑구'.split()
parts = []
raw_count = 0
for c in pd.read_csv(ROOT / 'data/raw/calltaxi/seoul_calltaxi_2025.csv', dtype=str,
                     encoding='utf-8-sig', chunksize=200000,
                     usecols=TIMES + ['출발구', '목적구', '이용목적']):
    raw_count += len(c)
    for col in TIMES:
        c[col] = pd.to_datetime(c[col], format='mixed', errors='coerce')
    purpose = c['이용목적'].str.strip()
    valid = c[TIMES[:5]].notna().all(axis=1) & c['취소일시'].isna()
    valid &= c['접수일시'].le(c['배차일시']) & c['배차일시'].le(c['승차일시']) & c['승차일시'].le(c['하차일시'])
    lead = (c['예정일시'] - c['접수일시']).dt.total_seconds() / 60
    valid &= lead.between(0, 1) & purpose.str.contains('치료|재활', na=False) & ~purpose.str.contains('예약', na=False)
    f = c.loc[valid].copy()
    f['origin'] = f['출발구'].str.strip()
    f['destination'] = f['목적구'].str.strip().fillna('미상')
    f['date'] = f['접수일시']
    f['hour'] = f['date'].dt.hour.astype(str)
    f['weekday'] = f['date'].dt.dayofweek.astype(str)
    f['hour_weekday'] = f['hour'] + '_' + f['weekday']
    f['wait'] = (f['승차일시'] - f['접수일시']).dt.total_seconds() / 60
    parts.append(f[['origin', 'destination', 'date', 'hour', 'weekday', 'hour_weekday', 'wait']])
assert raw_count == 1729476
all_records = pd.concat(parts, ignore_index=True)
data = all_records[all_records.origin.isin(DISTRICTS)].copy()
data['over60'] = data.wait.gt(60).astype(int)
benchmark = data.groupby('origin').agg(records=('wait', 'size'), over60_records=('over60', 'sum'),
    over60_pct=('over60', lambda s: 100 * s.mean()), p90_wait_min=('wait', lambda s: s.quantile(.9)))
benchmark['descriptive_rank_highest_burden_first'] = benchmark.over60_pct.rank(method='min', ascending=False).astype(int)
benchmark.sort_values('over60_pct', ascending=False).to_csv(OUT / 'citywide_same_cohort.csv')
selected = data[data.origin.isin(['중구', '성동구', '동대문구'])]
assert len(benchmark) == 25 and len(selected) == 6683 and selected.over60.sum() == 1374
assert benchmark.records.sum() == len(data) and benchmark.over60_records.sum() == data.over60.sum()

# Fixed specification; no search or test-driven model selection.
train = data[data.date.lt('2025-10-01')].copy()
test = data[data.date.ge('2025-10-01')].copy()
assert train.date.max() < test.date.min() and len(train) + len(test) == len(data)
features = ['origin', 'destination', 'hour', 'weekday', 'hour_weekday']
assert set(features).isdisjoint({'wait', 'over60', '배차일시', '승차일시', '하차일시', '차량구분'})
model = make_pipeline(ColumnTransformer([('request_known', OneHotEncoder(handle_unknown='ignore'), features)]),
                      LogisticRegression(C=1.0, max_iter=1000, random_state=0))
model.fit(train[features], train.over60)
groups = train.groupby('hour_weekday').over60.agg(['sum', 'count'])
# shortcut: fixed smoothing of 20 training records; re-evaluate on prospective data before deployment.
rates = (groups['sum'] + 20 * train.over60.mean()) / (groups['count'] + 20)
predictions = {
    'constant_training_rate': np.full(len(test), train.over60.mean()),
    'hour_weekday_training_rate': test.hour_weekday.map(rates).fillna(train.over60.mean()).to_numpy(),
    'logistic_request_known': model.predict_proba(test[features])[:, 1],
}
rows = []
for name, p in predictions.items():
    assert len(p) == len(test) and np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
    rows.append({'model': name, 'test_records': len(test), 'test_over60_records': int(test.over60.sum()),
                 'test_prevalence': test.over60.mean(), 'mean_predicted_risk': p.mean(),
                 'roc_auc': roc_auc_score(test.over60, p), 'average_precision': average_precision_score(test.over60, p),
                 'brier_score': brier_score_loss(test.over60, p)})
metrics = pd.DataFrame(rows)
metrics.to_csv(OUT / 'retrospective_temporal_metrics.csv', index=False)
subgroups = []
for label, mask in [('three_case_districts', test.origin.isin(['중구', '성동구', '동대문구']))] + [
        (f'month_{month}', test.date.dt.month.eq(month)) for month in [10, 11, 12]]:
    for name, p in predictions.items():
        y = test.loc[mask, 'over60']
        assert y.nunique() == 2
        subgroups.append({'subgroup': label, 'model': name, 'records': len(y),
            'over60_records': int(y.sum()), 'roc_auc': roc_auc_score(y, p[mask.to_numpy()]),
            'brier_score': brier_score_loss(y, p[mask.to_numpy()])})
pd.DataFrame(subgroups).to_csv(OUT / 'subgroup_metrics.csv', index=False)
calibration = test[['over60']].copy()
calibration['risk'] = predictions['logistic_request_known']
calibration['risk_band'] = pd.cut(calibration.risk, [-.001, .1, .2, .4, .6, 1.0])
calibration.groupby('risk_band', observed=True).agg(records=('over60', 'size'), predicted=('risk', 'mean'),
    observed=('over60', 'mean')).to_csv(OUT / 'logistic_calibration.csv')
metadata = {'raw_rows': raw_count, 'seoul_records': len(data), 'seoul_over60_records': int(data.over60.sum()),
    'seoul_over60_pct': 100 * data.over60.mean(), 'excluded_non_seoul_origin_records': len(all_records)-len(data),
    'train_records': len(train), 'test_records': len(test), 'train_end': str(train.date.max()), 'test_start': str(test.date.min()),
    'features': features, 'specification': 'One-hot logistic C=1; fixed, no tuning; empirical hour x day-of-week baseline smoothing=20',
    'scope': 'All 25 Seoul origins; same purpose/clean/lead cohort as main report; raw rates unadjusted for case mix',
    'validation': 'Retrospective chronological split Jan-Sep / Oct-Dec; the year was already explored, not untouched external validation',
    'limits': 'Completed requests only; no rider IDs; repeated riders and destinations; no causal or clinical-lateness inference; calibration drift possible',
    'policy_effect_verified': False}
(OUT / 'validation_scope.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
print(benchmark.round(3).to_string())
print(metrics.round(5).to_string(index=False))
print(json.dumps(metadata, ensure_ascii=False))
