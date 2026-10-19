# 망젤이네 재현 코드

## 먼저 읽을 파일

- [제출 본문 PDF](outputs/reports/망젤이네_분석보고서.pdf): 본문 5쪽 + 참고문헌 1쪽
- [분석 부록 PDF](appendix/망젤이네_분석부록.pdf): A1~A14, 근거·검증·가정·재현 안내 15쪽
- [일반 이용형 공동승차 검증 4쪽](outputs/reports/망젤이네_일반이용형_DRT_검증.pdf): 추가 가설 검증, 제출 본문과 별도
- [부록 파일별 안내](appendix/README.md): 원본 표와 코드로 이동
- [파일별 근거 인덱스](appendix/evidence_index.csv): 자료 성격·실행 코드·SHA-256

부록은 본문과 분리된 열람 자료입니다. docs의 날짜별 문서는 분석 과정의 상세 노트이며 최신 제출 결론은 본문 PDF와 부록을 기준으로 읽어주세요. 설명용 탄소 시나리오는 예상 성과·실증값이 아닙니다.


## 최종 제출본과 보조 시나리오
제출 기준 PDF는 outputs/reports/망젤이네_분석보고서.pdf입니다(본문 5쪽 + 참고문헌 1쪽). 약 0.95t 감소는 실측 또는 정책의 예상 성과가 아니라 설명용 보조 시나리오입니다. 탄소 가정의 근거는 outputs/tables/carbon_audit/assumption_evidence_register.csv를 확인하세요. 20번 계산과 21번 측정 코드는 가정·단위·입력을 검증하는 도구이며 실측 대체율·합승·공차의 존재를 입증하지 않습니다. 제출본은 실제 관측된 치료·재활 시간 부담, 기존 운영 개선의 우선 검증, 조건부 예약 실증을 중심으로 구성했습니다.


Python 3.13 기준입니다. 보고서의 주 분석은 2025년 장애인콜택시 기록입니다. 통신 OD는 보조 탐색이며 이 패키지의 핵심 집계에 합산하지 않습니다.

## 저장된 집계에서 빠른 재현
압축을 푼 최상위 폴더에서 다음을 실행합니다. 두 스크립트는 Python 표준 라이브러리만 사용합니다.

```sh
python notebooks/15_seoul_drt_policy_evidence.py
python notebooks/16_seoul_cost_advantage_check.py
```

## 원자료부터 재현
공공데이터포털 https://www.data.go.kr/data/15115859/fileData.do 에서 2025년 파일을 취득해 data/raw/calltaxi/seoul_calltaxi_2025.csv 에 배치합니다. 분석 파일은 338,587,487바이트, 1,729,476행입니다. 개인정보 및 대용량 원자료는 포함하지 않았습니다.

```sh
python -m pip install pandas numpy
python notebooks/12_public_service_necessity.py
python notebooks/13_vehicle_budget_screen.py
python notebooks/15_seoul_drt_policy_evidence.py
python notebooks/16_seoul_cost_advantage_check.py
```

12·13은 10번 전처리와 자체 검사를 실행합니다. 결과는 outputs/tables 아래에 저장됩니다. 집계 건수는 사람 수가 아닙니다. 용량 환산은 실제 수요·이용 실적이 아니며 비용 입력은 견적이 아닙니다.

보고서 원문과 그림은 docs에 포함합니다. 18번은 선택적인 PDF 생성 코드로 reportlab, pypdf, matplotlib, numpy 및 macOS AppleGothic 폰트가 필요합니다. 다른 운영체제에서는 FONT 경로를 한글 지원 폰트로 바꿔야 합니다. Word 편집본은 Pandoc으로 별도 생성했습니다.

외부 코드 열람 URL: https://github.com/kanginhan1018-gif/AI---
2026-10-19 공개 접근과 최상위 폴더 구성을 확인했습니다.

## 2026-10-19 보고서 보강
통신자료 기간 확대와 기존 후보의 변화는 outputs/tables/telecom_12weeks의 요약표·원자료 출처·독립 확인 기록으로 추적할 수 있습니다. 이 보조 탐색의 대용량 통신 원자료와 전체 처리 파이프라인은 이 패키지에 포함하지 않습니다. 위 실행 절차는 보고서 핵심인 이동지원 기록과 비용 계산을 대상으로 합니다.

보고서 생성 결과는 본문 5쪽과 참고문헌 1쪽입니다. 외부 코드 열람 주소는 보고서 원문에 반영했습니다.

## 탄소 검증 추가
`python notebooks/19_carbon_feasibility_audit.py`는 같은 2025년 원자료를 다시 읽어 승차거리를 검증합니다(pandas·numpy 필요). 산출물은 outputs/tables/carbon_audit에 저장됩니다. 승차거리와 조건부 환산은 탄소 감축 실증값이 아닙니다. 자세한 판정은 docs/2026-10-19-carbon-empirical-audit.md를 확인하세요. measurement_template.csv는 실제 운행·에너지 자료를 채울 빈 양식입니다.

## 자가용 대체 손익분기
`python notebooks/20_carbon_substitution_break_even.py`는 표준 라이브러리로 108개 가정 조합의 감축 손익분기 비중을 계산합니다. 실측 대체율·감축량이 아닙니다. docs/2026-10-19-carbon-alternative-validation.md에 단위·경계·해석을 설명했습니다.

## 측정 코드와 CSV 입력
`notebooks/21_carbon_measurement.py`는 CSV 입력으로 자가용 대체 비중·재차인원·공차 비율·에너지별 배출과 탄소 순변화를 계산합니다. 실행 명령·실측 입력 양식·검증 범위는 examples/carbon/README.md에 있습니다. 기본 예시는 가상 시나리오이며 약 0.95t 감축을 재현합니다. 실측자료와 인과 검증을 대신하지 않습니다. `python -m unittest discover -s tests -p test_carbon_measurement.py -v`로 6개 검사를 실행할 수 있습니다.

## 요일과 조건 변경 추가 검증
`python notebooks/22_treatment_robustness.py`는 동일 2025년 원자료로 10개 비교 조건을 재집계합니다(pandas 필요). 월~금 공휴일 포함·토일·차종·시간 허용조건·상하반기·시간축을 비교하며 자료 범위와 결과는 docs/2026-10-19-treatment-robustness-results.md와 outputs/tables/treatment_robustness에 있습니다. 요일 검산은 다른 CSV·datetime 구현으로도 확인했습니다. 새로운 자료의 예측 검증이나 정책의 인과효과 검증은 아닙니다. 최종 제출본은 이 결과를 반영해 요일별 운영 검증을 제안합니다.

## 정책·환경 검증 추가
`python notebooks/24_policy_environment_verification.py`는 공식 전체 평균, 원자료의 배차 단계 단축 민감도, 환경 검증의 미확인 조건을 구분합니다. pandas·numpy·pdftotext와 기존 원자료가 필요합니다. 상세 결과는 docs/2026-10-19-policy-environment-verification.md와 outputs/tables/policy_environment_verification에 있습니다. 공식 평균 감소·조건부 388건 감소는 이번 제안의 인과효과가 아닙니다. 실제 정책효과와 순탄소 감축량은 미확인(null)입니다.

## 서울 25개 구 비교와 후향적 위험 예측
`python notebooks/25_citywide_predictive_validation.py`를 실행합니다(pandas·numpy·scikit-learn 필요, scikit-learn 1.9.1에서 확인). 환경 목록은 environment.yml에 있습니다. 원자료 경로는 앞 절과 같습니다. 개별 예측은 공개하지 않고 구·월·모형별 집계만 outputs/tables/citywide_predictive_validation에 저장합니다.

같은 조건 서울 81,988건 대비 기존 세 구는 최악의 지역이 아닙니다. 1~9월 학습/10~12월 평가에서 서울 전체 AUC는 시간대 기준 0.845→회귀 0.868이지만 세 구는 0.866→0.868로 추가 이득이 작아 단순 기준을 우선 비교합니다. 이미 탐색한 연도의 시간 분할이며 외부 검증·정책 효과가 아닙니다. 세부 범위와 과소 예측은 부록 A9와 docs/2026-10-19-citywide-predictive-validation.md에 공개했습니다.

## 일반 이용형 공동승차 검증 추가
27번은 치료·재활과 같은 서비스의 전체 목적 기록을 비교하고, 일반 시민 통신 OD, 조건부 단가와 공차 포함 차량km를 따로 검증합니다. 전체 목적도 이동지원 기록이므로 일반 시민 모집단으로 부르지 않습니다. 시간당 완료 건수와 평균 동시 탑승을 구분합니다. 서울의 실제 전환율·합승·비용·혼잡 성과는 미확인입니다.

```sh
python notebooks/27_open_pooling_verification.py
python notebooks/28_open_pooling_independent_check.py
```

pandas와 2025년 콜택시 원자료가 필요합니다. 통신 대용량 집계가 없으면 패키지의 general_population_OD_INPUT_ALL_ELIGIBLE.csv와 해시로 상위 10개 OD를 재계산합니다. 이는 전체 조건부 OD 입력을 제공한 것이며 통신 원자료 282,842,077행의 재검증과 구분합니다. 원자료부터는 기존 07번의 84일 집계가 필요합니다. 패키지 입력 경로로 실행해 요청 겹침·단가·상위 OD·차량km 네 결과 표가 일치함을 확인했습니다.

영국 DfT 2025 보고서 원문 PDF를 data/raw/drt_cost_evidence에, 출처·쪽수·해시를 verification_scope.json에 포함했습니다. 영국의 이용·공차 실적은 서울 예측값이 아닙니다. 29번은 추가 검증 PDF 생성 코드이며 reportlab·pypdf 및 macOS AppleGothic 폰트가 필요합니다. 본문 5쪽+참고문헌 1쪽은 유지하고 상세 결과를 부록 A10에 연결했습니다.


## 서울 OD와 버스 노선 연결 보조 검토
- [OD·버스 연결 분석 PDF](outputs/reports/망젤이네_서울_OD_버스연결_검토.pdf): 4쪽
- [핵심 분석](docs/2026-10-19-transit-corridor-overlay.md): 통신 OD와 대표 정류장 비교에 더해 서울시 2026-09-02 노선별 정류장 순서 파일로 직접버스 경로를 추가 검증했습니다.
- [원본 노선 파일](data/raw/bus_routes_seoul_20260902.xlsx)과 [15,012개 OD별 순서 검증](outputs/tables/open_pooling_verification/pilot_long_OD_route_sequence_check.csv)을 포함합니다.
- 재현: `python notebooks/32_validate_static_bus_route_paths.py` (Python 3.13, pandas, numpy, openpyxl 필요). 통신 84일 원자료 자체는 용량상 제외하고, 필터된 OD 입력을 사용합니다.


정류장 순서로 단일 버스 경로 후보는 검증했지만, 환승·지하철을 포함한 실제 문-문 이동시간과 접근성은 미검증입니다. 서울시 OA-1092 환승경로 API는 이 분석에서 호출하지 않았고, OD별 파일 스크린은 대중교통 경로 부재나 DRT 효과를 뜻하지 않습니다.


서울 열린데이터광장 OA-1095의 버스 노선 API 페이지에는 기존 인증키만 사용 가능하고 신규 발급이 불가하다는 안내가 있습니다. 이번 보완은 인증키가 필요 없는 공개 노선별 정류장 순서 파일을 사용했습니다.


## 공식 양식 반영 및 최신 보강 (2026.10.19)
제출 본문은 공식 필수 항목 순서(분석 배경 및 목적, 활용 데이터, 분석과정 및 방법, AI 기술 활용, 분석 내용 및 결과, 정책제안 및 기대효과)로 정리했고, PDF는 본문 5쪽과 참고문헌 1쪽입니다.
부록 A13은 서울 427개 행정동 중심점의 버스·철도 접근 공백 보조 선별이며, A14는 AI 수요예측·공동배차 최적화의 후속 설계입니다. A14는 미구현·미실증 계획입니다.
A13 재현에는 notebooks/37_seoul_bus_stop_desert_screen.py와 함께 추가된 중심점·정류장·철도 좌표·배차 입력 파일이 필요합니다.
