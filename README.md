# 망젤이네 재현 코드

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

이 ZIP 자체는 공모전에서 요구하는 외부 코드 열람 URL을 대신하지 않습니다. 제출자는 GitHub 또는 클라우드에 업로드한 뒤 보고서에 URL을 추가해야 합니다.
