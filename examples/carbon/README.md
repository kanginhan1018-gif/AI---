# 탄소 추정 재현과 운행자료 측정

## 설명용 추정치 재현

저장소 최상위에서 Python 3.11 이상으로 실행합니다. 외부 패키지는 필요 없습니다.

```sh
python notebooks/21_carbon_measurement.py --input examples/carbon/scenario_inputs.csv --factors examples/carbon/illustrative_factors.json --data-kind scenario --output-dir outputs/tables/carbon_measurement_demo
```

결과는 CSV와 JSON입니다. 3명 합승 가정의 `net_reduction_tco2eq_negative_is_increase`가 0.9485705285로 계산됩니다. 양수는 감소, 음수는 증가입니다. sample의 기간 2025년은 역사적 거리 기준 규모를 표시하며 실제 DRT가 그 기간 운행했다는 뜻이 아닙니다. JSON은 입력·계수·배출 경계를 함께 남깁니다. 대안 시나리오와 겹치는 기간을 자동 합산하거나 연간으로 외삽하지 않습니다.

## 실제 운행자료 입력

`operational_measurement_template.csv`를 복사해 기관이 확인한 비교 집합·기간의 자료를 채웁니다. 빈 양식은 0톤으로 처리하지 않습니다.

| 항목 | 정의 |
|---|---|
| measurement_id | 중복 없는 측정 식별자. 이름·전화번호·차량번호가 필요하지 않음 |
| period_start, period_end | 비교하는 집계 기간. 기준선·개선 후의 에너지 귀속과 대상 범위를 맞출 것 |
| scope_ref | 지원 수준·대상 집합·비교 방법을 설명한 근거 문서 위치 |
| reference_trip_km | 전체 대상 이용자의 기준경로 거리 합계. 동일 집합의 거리 비중 분모 |
| car_replaced_reference_km | 자가용 운행 대체로 귀속한 기준경로 거리. 보호자 회송을 가산하지 않는 범위 |
| drt_target_passenger_km | 동행 보호자를 제외한 대상 이용자의 실제 탑승거리 합계 |
| drt_loaded_vehicle_km | 대상 이용자가 탑승한 차량의 거리. 합승 시 차량 구간 중복 합산 금지 |
| drt_empty_vehicle_km | 같은 서비스 경계의 접근·회송·공차 차량거리 |
| baseline_car_energy_type, unit, amount | 회피했다고 추정한 자가용 운행에 귀속한 기준선 에너지. 사라진 연료를 직접 계량했다는 뜻이 아님 |
| drt_energy_type, unit, amount | 비교 대상 서비스 운행의 추가 에너지 사용. 다른 사업·정비와의 배분 근거 필요 |
| substitution_evidence_ref | 자가용 대체를 판단한 기록·비교 분석의 근거 위치 |
| baseline_energy_evidence_ref | 비교 가능한 과거 연료·계측 자료 및 회피 운행에 귀속한 계산의 근거 |
| drt_energy_evidence_ref | 주유·충전 또는 계측 및 서비스 배분의 근거 |

실제 입력 예시 명령(파일은 사용자가 실제 자료로 작성해야 함):

```sh
python notebooks/21_carbon_measurement.py --input actual_measurements.csv --factors verified_factors.json --data-kind operational --output-dir outputs/tables/carbon_operational
```

계수 JSON의 형식은 `illustrative_factors.json`을 참고합니다. 실제 분석에서는 적용 연도·차종·경계에 맞춰 검토한 계수와 출처로 교체합니다. 전기차는 실제 kWh와 일관된 전력 계수를 입력해야 하며 배출량 0으로 자동 처리하지 않습니다. 기본 예시는 과거 생활 실천용 계수로 실제 차량 인벤토리 검증을 대신하지 않습니다.

## 자동 계산과 검증 범위

- 거리 기준 자가용 대체 비중 = 대체 기준경로 거리 / 전체 기준경로 거리
- 거리 가중 평균 대상 재차인원 = 대상 이용자 탑승거리 합계 / 승차 차량거리
- 공차/승차거리 비율 = 공차 차량거리 / 승차 차량거리
- 기준 대비 탑승거리 변화 = 대상 탑승거리 / 기준경로 거리 − 1
- 탄소 순감축 = 귀속한 자가용 기준선 에너지 배출 − 서비스 추가 에너지 배출

`reference_trip_km`과 실제 탑승거리의 집합이 다르면 우회율이나 재차인원을 해석할 수 없습니다. 동행 보호자를 독립적인 자가용 대체 이용자로 세지 않습니다. 다른 수단의 회피 배출과 차량 제조·연료 공급 상류 등은 포함한 모델이 아니므로 전체 정책 효과와 구분합니다.

입력 근거의 존재·내용, 배분 타당성, 비교집합·서비스 수준 동일성은 코드가 인증하지 않습니다. operational 모드에서도 `causal_reduction_verified`는 false로 유지합니다. 파일명이나 증빙 경로가 있다는 사실만으로 인과적 감축을 검증했다고 판정하지 않습니다. 실측 입력이 없으면 제공한 시나리오 결과만 얻을 수 있습니다.

## 검사

```sh
python -m unittest discover -s tests -p test_carbon_measurement.py -v
```

계산 재현, 음수·비유한 값·잘못된 거리 범위, 단위 불일치, 근거 누락, 빈 양식, 중복 식별자를 검사합니다.
