"""Build a four-page evidence note; does not replace the competition main PDF."""
from pathlib import Path
import csv
import html
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/reports';OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/'outputs/tables/open_pooling_verification'
def rows(name):return list(csv.DictReader((DATA/name).open()))
def mdtable(headers,body):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(map(str,r))+' |' for r in body])
coocc=rows('service_cooccurrence.csv');cost=rows('conditional_unit_cost.csv');top=rows('general_population_top10_OD_NOT_DRT_DEMAND.csv')
thresholds=json.loads((DATA/'cost_thresholds.json').read_text())
assert len(coocc)==24 and len(cost)==12 and len(top)==10
selected=[r for r in coocc if r['minutes']=='30' and r['bin_offset_minutes']=='0']
labels={'destination_dong':'목적지 동 일치','origin_district_destination_dong':'출발 구·목적지 동 일치','origin_dong_destination_dong':'출발 동·목적지 동 일치'}
comparison=[]
for key,label in labels.items():
 a=next(r for r in selected if r['cohort']=='treatment' and r['screen']==key)
 b=next(r for r in selected if r['cohort']=='all_purposes_same_service' and r['screen']==key)
 comparison.append([label,f'{int(a["records_in_2plus"]):,}건 / {float(a["share_pct"]):.2f}%',f'{int(b["records_in_2plus"]):,}건 / {float(b["share_pct"]):.2f}%'])
pages=["""# 일반 이용형 공동승차 DRT 검증

망젤이네 | 2026.10.19 | 제출 본문을 보완하는 추가 검증 자료

## 1 판정과 실제 기록의 검증

**판정: 이용 범위를 넓히면 공동승차 후보가 늘어날 가능성은 확인했다. 서울에서 운영 단가와 교통체증이 실제로 감소한다는 주장은 아직 입증되지 않았다.** 요청 증가, 공동승차, 자가용 대체는 서로 다른 조건이다.

### 같은 조건에서 이용 목적을 넓혀 비교

2025년 원자료 1,729,476행에서 정상 완료·예약 명칭 제외·예정−접수 0~1분·세 구 출발 조건을 유지했다. 치료·재활 6,683건과 전체 목적 100,222건을 비교했다. 접수 날짜와 시각을 30분 단위로 나눠 2건 이상이 있는 묶음의 기록 수를 집계했다. 전체 목적도 장애인콜택시 이용 기록이며 일반 시민 전체가 아니다.

"""+mdtable(['겹침 조건','치료·재활 6,683건','전체 목적 100,222건'],comparison)+"""

목적지를 같게 둔 경우 겹침 비율은 증가했지만, 출발 동까지 같게 두면 1.93%→1.98%로 거의 같았다. **이용 규모 확대만으로 가까운 출발지와 공통 목적지가 충분히 확보된다고 볼 수 없다.** 넓은 권역에서 요청을 모으면 우회·접근시간도 늘 수 있다.

### 이 집계가 합승 가능률은 아닌 이유

같은 동은 같은 병원·주소를 뜻하지 않는다. 별도 이용자 ID가 없어 서로 다른 사람인지 확정하지 못한다. 실제 승차를 기다릴 의사, 도착 기한, 동의, 휠체어 공간과 승하차 지원도 확인하지 못했다. 고정 시간 구간은 경계 양쪽의 가까운 요청을 놓칠 수 있어 15·30·60분과 30분 구간의 15분 이동 조건도 저장했다. 시간 간격을 넓힌 결과를 실제 허용 대기시간으로 해석하지 않는다.

원자료를 Python CSV·datetime으로 별도 재집계해 출발 구·목적지 동 조건의 308건과 8,010건이 일치했다. 본 결과는 관측된 겹침 검증이며 운행 경로 모의실험이 아니다.
""",
"""## 2 일반 시민의 이동 규모와 단가 조건

### 통신자료의 전체 연령 이동을 별도로 확인

2026.07.06~09.27의 기존 84일 집계에서 일반 평일 56일 오전 7~9시 출발, 서울 내 다른 동으로 향하는 단방향 OD를 비교했다. 전체 연령 이동이 큰 상위 10개 연결에서 전체 연령 규모는 60세 이상 규모의 약 2.80~6.33배였다. 이는 모집단 확대 가능성을 보여주는 통행량이며 DRT 이용률·자가용 대체율이 아니다. 2025년 서비스 기록과 개인별로 결합하지 않았다.

"""+mdtable(['출발 → 도착 동','전체 연령 / 평일 오전','60세 이상 / 평일 오전'],[
 [r['origin_name'].replace('서울특별시 ', '')+' → '+r['destination_name'].replace('서울특별시 ',''),f'{float(r["all_age_mean_weekday_07_10_trips"]):,.1f}',f'{float(r["age60plus_mean_weekday_07_10_trips"]):,.1f}'] for r in top[:3]])+"""

기존 버스·철도·도보를 포함할 수 있고 실제 시설이나 신규 이용 의사는 알 수 없다. 상위 이동량만으로 도입 구간을 선정하거나 기존 대중교통을 대체하지 않는다.

### 실제 사례로 범위를 점검한 조건부 단가

영국 DfT의 18개 농촌·교외 DRT 평가에서 차량시간당 이용은 0.9~3.9건, 사업별 평균은 2.1건이었다[1]. 서울의 보장값이 아닌 민감도 범위로만 사용했다. 기존 계획 가정인 연 반복비 1억4,500만원과 연 1,825 차량시간을 고정하면 다음과 같다. 구매·준비비는 제외했다.

"""+mdtable(['가정 이용 / 전체 차량시간','기존 반복비 / 건','비용 20% 증가 / 건'],[
 [q, f'{float(next(r for r in cost if r["assumed_completed_journeys_per_covered_vehicle_hour"]==q and float(r["cost_multiplier"])==1)["conditional_cost_per_journey_krw"]):,.0f}원',f'{float(next(r for r in cost if r["assumed_completed_journeys_per_covered_vehicle_hour"]==q and float(r["cost_multiplier"])==1.2)["conditional_cost_per_journey_krw"]):,.0f}원'] for q in ['0.9','2.1','3.9']])+"""

기존 비용 가정에서 과거 콜택시 평균 59,700원에 맞추려면 시간당 1.33건, 법인특장택시 평균 44,025원에는 1.80건이 필요하다. 20% 비용 증가 시 각각 1.60·2.17건이다. 과거 평균은 현재 같은 서비스의 추가 원가가 아니므로 비용 우위의 확정 기준이 아니다.

**시간당 완료 건수는 동시에 탄 인원과 다르다.** 이용 증가에 따른 차량·인력 증원, 지원시간과 우회가 비용을 높일 수 있으므로 단가 하락을 고정 예산으로 보장하지 않는다.
""",
"""## 3 차량 통행량과 혼잡 완화 조건

### 공차를 포함해야 자가용 대체 효과를 판단할 수 있다

새 일반 이용형 DRT의 직접 이동거리 합계를 P, 그중 자가용에서 전환한 사람 이동거리 비중을 p, 기존 자가용 평균 탑승을 m, DRT 승객의 거리 가중 평균 동시 탑승을 n, 우회를 d, 공차/승객 탑승 운행거리 비율을 e로 둔다. n은 우회를 포함한 승객km/승객 탑승 차량km이며, 앞쪽의 시간당 완료 건수와 다르다.

추가 DRT 차량km = P × (1+d) × (1+e) / n

회피 자가용 차량km = P × p / m

따라서 차량km 순감소에는 **p > m × (1+d) × (1+e) / n**이 필요하다. 기존 버스 운행은 유지하고 도보·철도·버스 전환의 회피 차량km는 0으로 둔다. 기존 콜택시 운행을 대체하는 별도 기준선과 혼합하지 않는다.

### 공개 실적의 공차 수준을 넣은 민감도

영국 평가의 사업별 공차/유인거리 평균은 0.77, 범위는 0.45~1.09였다[1]. 서울에서 관측한 값은 아니다. e=0.77, 우회 d=10%를 가정한 손익분기는 다음과 같다.

"""+mdtable(['DRT 평균 동시 탑승 n','자가용 1명 m=1','자가용 1.3명 m=1.3'],[
 ['2명','자가용 전환 비중 97.35% 초과','126.56% 초과: 이 조건에서는 불가'],['3명','64.90% 초과','84.37% 초과'],['4명','48.68% 초과','63.28% 초과']])+"""

n·우회·자가용 전환·기존 탑승은 미검증 가정이다. 운전자와 비독립 동반자는 효과를 부풀리는 신규 요청으로 세지 않는다. 같은 지원 수준에서 확보할 수 있는 실제 탑승량으로 검증해야 한다.

직접 승객거리 1,000km당 자가용 전환 70%, 기존 자가용 1명, DRT 평균 동시 탑승 3명이면 추가 DRT 649km·회피 자가용 700km로 51km 감소한다. 그러나 DRT 탑승이 2명이면 973.5km로 273.5km 증가한다. DRT 3명이어도 기존 자가용 탑승이 1.3명이면 회피는 538.5km여서 110.5km 증가한다. 실제 수요나 서울 전체 감축량으로 환산하지 않았다.

### 차량km 감소와 교통체증 감소는 다르다

혼잡은 도로 구간·시각별 유입, 교차로 용량, 정차와 차량 크기의 영향을 받는다. 총 차량km가 줄어도 첨두 혼잡이 줄었다고 단정할 수 없다. 본 계산은 288개 가정 조합의 회계적 민감도이며 네트워크 배정·교통 모의실험이 아니다. 영국 평가도 수단 전환의 직접 귀속 증거가 부족하다고 밝혔다[1].
""",
"""## 4 설문 없이 다음 단계까지 검증하는 방법

### 권역을 제한한 공동승차 실증

의료·재활 이동지원 개선을 중심에 두고, 지원을 유지할 수 있는 일반 이용 요청을 같은 거점·시간대에 묶는 확장안을 비교한다. 의료 목적이나 연령만으로 배차 우선순위를 자동 부여하지 않는다. 역·병원 등 거점의 정확한 승하차 위치와 도착시간을 확인하고, 기존 대중교통 연결이 부족한 경우부터 대안을 비교한다.

1. 기존 이용자 지원·승차 공간과 예약 도착 기한을 먼저 제약조건으로 둔다. 일반 요청을 추가하면서 기존 이용자의 대기·우회·거절이 늘어나는지 확인한다.

2. 실제 예약·차량 GPS로 합승 유지거리, 공차·총주행거리, 완료 건수와 전체 차량시간을 측정한다. 주유·충전량과 실제 증분비용도 함께 수집한다. 승인된 데이터만 최소 범위로 사용한다.

3. 설문을 쓰지 않는다면 동의한 참여자의 도입 전후 이동 궤적과 주차 출입 기록 등으로 자가용 이용 변화를 확인한다. 자료가 없으면 자가용 전환율을 식별할 수 없다고 보고한다. 정류장·역 인근 이용이라는 이유만으로 자가용 대체를 인정하지 않는다.

4. 도입 전 비교 기간을 정하고 비슷한 요일·시각의 비교 구간과 교통량·통행시간을 함께 측정한다. 단계적 도입 시 비교군 추세·도로 공사·행사·계절 변화를 점검한다. 단순 전후 차이는 인과효과로 확정하지 않는다.

### 채택 판단

같은 지원 수준을 유지하면서 실제 추가 지출/완료 이동이 개선되면 비용효율 성과로 보고한다. 자가용 회피 차량km가 DRT 추가 차량km를 초과하면 차량 통행 감소 근거로 보고하되, 혼잡 개선은 구간별 교통량·통행시간 결과로 별도 판정한다. 단가 하락만으로 교통체증·탄소 감축을 동시에 주장하지 않는다.

**현재 제안: 일반 시민에게 전면 개방하면 효율화된다는 결론 대신, 거점·시간대가 맞는 요청을 추가하는 공동승차의 조건부 실증으로 채택한다.** 서울의 실제 일반 이용 수요·합승 제약·견적·자가용 전환 자료가 확보되기 전에는 차량 구매 규모나 혼잡 감소 수치를 확정하지 않는다.

### 출처와 재현

[1] UK Department for Transport. Rural Mobility Fund phase 1 evaluation: final report. 2025.12.17. PDF 53쪽(본문 37쪽): 차량시간당 이용·공차, PDF 86쪽(본문 70쪽): 수단 전환 증거 한계. https://www.gov.uk/government/publications/rural-mobility-fund-phase-1-evaluation-final-report

[2] 같은 기관의 DRT 운영 지침. 2025.12.17. 기존 교통망과의 연계·운영비·공차 점검. https://www.gov.uk/government/publications/demand-responsive-transport/demand-responsive-transport

서울 탑승내역·통신 OD·비용 원문은 기존 제출 본문 [1]·[2]·[4]와 같다. 분석: 27번. 별도 CSV·datetime 검산: 28번. PDF: 29번. 결과: outputs/tables/open_pooling_verification. 통신 원자료 검증에는 07번의 84일 원천 집계가 필요하다. ZIP에서는 해당 조건의 전체 OD 입력 표와 해시로 상위 10개 연결을 재현하며, 대용량 원자료 재검증과 구분한다.
"""]
source='\n\n<!-- pagebreak -->\n\n'.join(pages)
(ROOT/'docs/2026-10-19-open-pooling-verification.md').write_text(source)
pdfmetrics.registerFont(TTFont('Korean','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
base=dict(fontName='Korean',wordWrap='CJK',textColor=colors.HexColor('#20323e'))
styles={k:ParagraphStyle(k,**v,**base) for k,v in {
 'body':dict(fontSize=10,leading=15.2,spaceAfter=8), 'h1':dict(fontSize=17,leading=23,spaceAfter=12),
 'h2':dict(fontSize=14,leading=20,spaceAfter=12), 'h3':dict(fontSize=11,leading=16,spaceAfter=6,spaceBefore=6,keepWithNext=True),
 'cell':dict(fontSize=9,leading=13)}.items()}
def para(s,style='body'):
 import re
 t=html.escape(s);t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t)
 return Paragraph(t,styles[style])
story=[]
for page_no,page in enumerate(pages):
 if page_no:story.append(PageBreak())
 lines=page.splitlines();i=0
 while i<len(lines):
  line=lines[i].strip();i+=1
  if not line:continue
  if line.startswith('|'):
   records=[line]
   while i<len(lines) and lines[i].strip().startswith('|'):records.append(lines[i].strip());i+=1
   records=[r for r in records if not set(r)<=set('|- :')]
   cells=[[para(c.strip(),'cell') for c in row.strip('|').split('|')] for row in records]
   assert all(len(r)==3 for r in cells)
   t=Table(cells,colWidths=[180,161,161],repeatRows=1)
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#bdcbd4')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
   story.extend([t,Spacer(1,9)]);continue
  if line.startswith('#'):
   level=len(line)-len(line.lstrip('#'));story.append(para(line.lstrip('# '),'h'+str(level)))
  else:story.append(para(line))
def footer(canvas,doc):
 canvas.setFont('Korean',8);canvas.drawString(46,815,'망젤이네 · 일반 이용형 공동승차 추가 검증');canvas.drawRightString(549,28,str(doc.page))
pdf=OUT/'망젤이네_일반이용형_DRT_검증.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=46,rightMargin=46,topMargin=43,bottomMargin=43,title='일반 이용형 공동승차 DRT 검증',author='망젤이네').build(story,onFirstPage=footer,onLaterPages=footer)
r=PdfReader(pdf);assert len(r.pages)==4,len(r.pages)
for i,p in enumerate(r.pages):assert f'{i+1} ' in p.extract_text()
print(pdf)
