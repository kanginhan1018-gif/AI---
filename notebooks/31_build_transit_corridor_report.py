"""Build a three-page OD and representative bus-network screen."""
from pathlib import Path
import csv,html
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/reports';OUT.mkdir(parents=True,exist_ok=True)
T=ROOT/'outputs/tables/open_pooling_verification'
I=ROOT/'outputs/tables/integrated_corridor_screen'
def table(h,rs):return '\n'.join(['| '+' | '.join(h)+' |','|'+'---|'*len(h)]+['| '+' | '.join(map(str,r))+' |' for r in rs])
x=pd.read_csv(T/'pilot_morning_OD_bus_overlay.csv',dtype={'o_admdong_cd':str,'d_admdong_cd':str})
meta=__import__('json').loads((T/'transit_overlay_scope.json').read_text())
known=x[x.origin_bus_connectivity_screen.ne('coverage missing')]
shared=known[known.origin_bus_connectivity_screen.eq('representative route shared')]
unshared=known[known.origin_bus_connectivity_screen.eq('no representative shared route')]
assert len(x)==28744 and len(known)==18569 and len(shared)==377
assert abs(known.mean_weekday_07_10_all_age.sum()-227628.46714285715)<.01
assert abs(unshared.mean_weekday_07_10_all_age.sum()-208646.5285714286)<.01
bands=pd.read_csv(T/'pilot_OD_bus_distance_screen.csv')
long=unshared[unshared.straight_line_centroid_km.ge(5)].nlargest(6,'mean_weekday_07_10_all_age')
assert len(long)==6 and long.straight_line_centroid_km.min()>=5
spatial=pd.read_csv(I/'all_corridors_with_transit_proxies.csv',dtype={'o_admdong_cd':str,'d_admdong_cd':str})
cohort=unshared[unshared.straight_line_centroid_km.ge(5)].merge(spatial,on=['o_admdong_cd','d_admdong_cd'],validate='one_to_one')
assert len(cohort)==15012 and cohort.mean_weekday_07_10_all_age.ge(0).all()
assert cohort.origin_all_bus_stops_500m.gt(0).mean()==1
assert round(cohort.destination_all_bus_stops_500m.gt(0).mean()*100,1)==97.4
assert cohort.origin_nearest_fastest_headway_min.median()==9 and cohort.destination_nearest_fastest_headway_min.median()==10
examples=cohort.set_index(['origin_name','destination_name'])
assert round(examples.loc[('서울특별시 동대문구 이문1동','서울특별시 종로구 종로1.2.3.4가동'),'origin_all_bus_stops_500m'])==20
cohort[['o_admdong_cd','d_admdong_cd','origin_name','destination_name','mean_weekday_07_10_all_age','mean_weekday_07_10_60plus','straight_line_centroid_km','origin_all_bus_stops_500m','destination_all_bus_stops_500m','origin_sampled_nearby_fastest_500m_min','destination_sampled_nearby_fastest_500m_min','common_sampled_route_count']].to_csv(T/'pilot_long_OD_stop_supply_check.csv',index=False)
route_check=pd.read_csv(T/'pilot_long_OD_route_sequence_check.csv',dtype={'o_admdong_cd':str,'d_admdong_cd':str})
assert len(route_check)==15012 and route_check.direct_bus_route_found_within_500m.sum()==3431
direct_flow=route_check.loc[route_check.direct_bus_route_found_within_500m,'mean_weekday_07_10_all_age'].sum()
assert abs(direct_flow-27913.61732142857)<.01
long=long.merge(route_check[['o_admdong_cd','d_admdong_cd','direct_bus_route_found_within_500m','direct_route_names','direct_route_ids']],on=['o_admdong_cd','d_admdong_cd'],validate='one_to_one')
pages=["""# 서울 오전 이동 OD와 버스 노선 연결 분석

망젤이네 | 2026.10.19 | 기존 세 구 일반 이용형 DRT 추가 탐색

## 1 통신 OD에 대표 정류장 버스 공급을 연결

2026년 7월 6일~9월 27일 통신 OD에서 세 구 출발·서울 내 다른 행정동 도착의 평일 7~9시 평균 이동량을 집계했다. 56개 평일의 시간별 평균을 합산했으며, 행정동 내부 이동은 제외했다. OD는 통행량 추정치이며 고유 사람 수나 이용수단이 아니다.

각 동의 대표 버스 정류장·도보 경로·정류장별 버스노선 ID·노선별 관측 배차간격을 2026년 공식 행정동 이름으로 연결했다. 두 동 대표 정류장에 같은 노선 ID가 있는지만 확인했다. 노선 ID 불일치는 직행 버스가 없다는 증명이 아니며 환승·지하철·전체 경로를 판단하지 못한다.

### 확인된 통행량과 노선 ID 겹침

"""+table(['대표 정류장 비교 결과','OD 쌍 수','평일 오전 평균 통행량','60세 이상 평균 통행량'],[
 ['두 대표 정류장에 공통 노선 ID',f'{len(shared):,}',f'{shared.mean_weekday_07_10_all_age.sum():,.0f}',f'{shared.mean_weekday_07_10_60plus.sum():,.0f}'],
 ['공통 노선 ID 미확인',f'{len(unshared):,}',f'{unshared.mean_weekday_07_10_all_age.sum():,.0f}',f'{unshared.mean_weekday_07_10_60plus.sum():,.0f}'],
 ['출발 또는 도착 대표 정류장 매칭 미확인',f'{len(x)-len(known):,}',f'{x.loc[x.origin_bus_connectivity_screen.eq("coverage missing"),"mean_weekday_07_10_all_age"].sum():,.0f}',f'{x.loc[x.origin_bus_connectivity_screen.eq("coverage missing"),"mean_weekday_07_10_60plus"].sum():,.0f}']])+"""

양쪽 대표 정류장 노선 ID가 확인된 통행량 중 91.66%가 양쪽 ID의 공통 노선을 찾지 못했다. 이는 ‘대중교통 연결이 없음’으로 해석할 수 없다. 60세 이상 집계도 교통약자 판정이나 해당 서비스 이용 예상량이 아니다.

모든 출발 동의 대표 정류장 자료가 2026 crosswalk에 연결되지는 않았다. 2023년 지리·정류장 파일과 2026 행정동 표기가 다른 동대문구 용신동은 미연결로 남겼다. 전체 OD 쌍의 64.60%만 양쪽 대표 정류장에 노선 자료가 있어 미연결 결과를 분모에서 조용히 제거하지 않았다.
""",
"""## 2 DRT 후보 검토가 필요한 OD를 더 좁힘

공통 노선 ID가 없는 쌍 중 행정동 중심점 직선거리가 5km 이상인 것은 15,012개 쌍, 평일 오전 평균 88,084통행(60세 이상 집계 13,710)이었다. 5km는 탐색을 위한 거리 구간이며 사업 적격 기준이 아니다. 직선거리도 실제 승객 경로·도로 거리와 같지 않다.

"""+table(['출발 → 도착 동','평일 오전 통행','60세 이상','중심점 직선거리','출발 대표 정류장 도보 / 노선 수'],[
 [r.origin_name.replace('서울특별시 ','')+' → '+r.destination_name.replace('서울특별시 ',''),
  f'{r.mean_weekday_07_10_all_age:,.1f}',f'{r.mean_weekday_07_10_60plus:,.1f}',f'{r.straight_line_centroid_km:.1f}km',
  f'{r.origin_stop_walk_min:.1f}분 / {int(r.origin_nearest_bus_route_count)}개'] for r in long.itertuples()])+"""

이 사례들의 출발 동 대표 정류장은 도보 추정 1.0~3.2분, 노선 수 1~6개, 노선별 간격 중앙값 9~11분이었다. 한 개 대표 정류장의 표본이므로 각 동의 모든 거주지 접근성이나 시간대별 운행 품질을 뜻하지 않는다. 우선 의심해야 할 문제는 ‘정류장까지 멀다’보다 목적지까지 노선 연결·환승·총 이동시간이다.

"""+table(['직선거리 구간','공통 노선 ID 미확인 OD 쌍','평일 오전 평균 통행량','60세 이상 평균 통행량'],[
 [str(r.centroid_distance_band),f'{int(r.OD_pairs):,}',f'{r.mean_weekday_all_age_trips:,.0f}',f'{r.mean_weekday_60plus_trips:,.0f}'] for r in bands[bands.origin_bus_connectivity_screen.eq('no representative shared route')].itertuples()])+"""

가까운 OD도 많아 DRT는 도보·직행버스·환승·고정 노선 보강과 비교해야 한다. 특히 0~2km 구간을 승차 수요나 교통약자 이동곤란의 증거로 쓰지 않는다.
""",
"""## 3 정책 판단과 다음 검증

### 현재 근거로 말할 수 있는 내용

평일 오전에 규모가 큰 일부 장거리 OD는 양쪽 동의 대표 정류장에서 공통 노선 ID가 확인되지 않아 **노선 경로를 추가 조사할 가치**가 있다. 그러나 실제 환승 경로가 없거나 DRT가 더 빠르고 경제적이라고 확정하지 않았다. 출발지 대표 정류장은 대체로 가깝고 여러 노선이 관측돼 일반 DRT가 기존 대중교통을 중복할 위험도 함께 있다.

### 다음 자료로 대안 간 차이를 가린다

1. 버스노선 정류장 순서·방향·요일별 시간표와 실제 도로망 경로를 사용해 각 상위 OD의 현재 최소 환승 경로·예상시간을 계산한다. 버스 노선 ID만 교차하는 화면은 충분하지 않다.

2. 지하철역 출입구·보행 연결과 교통약자 무장애 동선도 결합한다. 승차 수단별 관측이 없어 OD 규모만으로 고정 버스와 DRT를 선택하지 않는다.

3. 통신 OD의 더 긴 기간과 다른 계절에서 같은 구간의 시간대별 순위가 반복되는지 확인한다. 이 단계를 마치기 전 84일 통행량을 연간 수요로 환산하지 않는다.

4. 후보 구간의 예약형 공동승차를 실제 운영한다면 예약·수락·거절·탑승·우회·공차·차량시간·비용을 기록한다. 기존 버스·도보·택시에서 전환한 비중은 자료가 없으면 미확인으로 둔다.

### 분석 범위와 재현 자료

원 OD는 84일 중 평일 56일이며, 버스 정류장 노선자료의 조회 시점 및 시간대 유효성은 원 CSV에 기록되지 않았다. 행정동 대표점 직선거리와 대표 정류장 한 곳은 작은 공간 단위의 잠재적 접근성 차이를 가린다. ‘대표 노선 공통 ID 없음’은 스크리닝 신호이지 미운행·환승곤란 확정값이 아니다.

실행 코드: notebooks/30_transit_corridor_overlay.py. 필터된 OD 입력·출력·노선 정류장 소스 및 파일 해시는 공개 패키지에서 확인한다. 사용한 원천기간·해석 제한은 outputs/tables/open_pooling_verification/transit_overlay_scope.json에 기록했다. 통신자료 개인 연결이나 이용수단 판별은 하지 않았다.
"""]
pages.append("""## 4 보완 검증: 실제 버스 노선 순서 파일 대조

키 발급 대신 서울 열린데이터광장의 버스 노선 정보 **파일**(2026.09.02)을 내려받아 노선별 정류장 순번을 확인했다. 장거리 후보 15,012쌍 각각에 대해 행정동 중심점 500m 안 정류장을 출발·도착 후보로 놓고, 한 노선에서 출발 정류장 순번이 도착 정류장보다 앞서는지 검사했다. 원자료는 41,688개 노선-정류장 순서행, 718개 노선, 12,897개 고유 정류장으로 구성된다.

그 결과 **3,431쌍(22.9%)**에서 직접 버스 노선 순서를 찾았다. 해당 OD의 평일 오전 평균은 27,914통행으로 후보 집단 88,084통행의 31.7%다. 기존 대표 정류장 한 곳씩만 비교했을 때 공통 노선이 없던 일부 쌍도, 반경 내 다른 정류장 조합으로 직접 노선이 확인됐다. 그러므로 기존 대표정류장 스크린은 직접노선 부재를 과대 표시할 수 있었다.

"""+table(['출발 → 도착 동','통행량 (60세 이상)','거리','노선 파일 순번 확인'],[[
 r.origin_name.replace('서울특별시 동대문구 ','')+' → '+r.destination_name.replace('서울특별시 ','').replace('종로구 ','').replace('중구 ',''),
 f'{r.mean_weekday_07_10_all_age:,.0f} ({r.mean_weekday_07_10_60plus:,.0f})',f'{r.straight_line_centroid_km:.1f}km',
 ('직접 후보: '+str(r.direct_route_names).replace('|',' / ')) if r.direct_bus_route_found_within_500m else '500m 안에서 미검출'] for r in long.itertuples()])+"""

전농1동→종로1·2·3·4가동은 272번이 청량리미주아파트·동대문세무서(순번 16)에서 창덕궁·우리소리박물관(64)까지 이어진다. 이문1동→명동은 261번, 전농1동→명동은 105·202·261·262번이 각각 노선 순서상 연결된다. 반면 표의 이문1동·답십리1동·답십리2동→종로 통행은 동 중심점 500m 범위에서 단일 버스 노선이 검출되지 않았다.

이 결과는 **대중교통 경로 없음**의 판정이 아니다. 500m 밖 정류장, 버스 환승, 지하철, 실제 보행 가능 경로와 소요시간은 검증하지 않았다. OD 15,012쌍 모두의 순서검사 결과와 정류장별 근거는 `pilot_long_OD_route_sequence_check.csv` 및 `pilot_long_OD_direct_bus_route_evidence.csv`에 제공한다. 파일 출처는 서울시 열린데이터광장 OA-1095, `서울시버스노선별정류소정보(20260902).xlsx`다.
""")
source='\n\n<!-- pagebreak -->\n\n'.join(pages)
(ROOT/'docs/2026-10-19-transit-corridor-overlay.md').write_text(source)
pdfmetrics.registerFont(TTFont('Korean','/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
base=dict(fontName='Korean',wordWrap='CJK',textColor=colors.HexColor('#20323e'))
styles={k:ParagraphStyle(k,**v,**base) for k,v in {'body':dict(fontSize=9.8,leading=15,spaceAfter=7),'h1':dict(fontSize=17,leading=22,spaceAfter=12),'h2':dict(fontSize=14,leading=19,spaceAfter=10),'h3':dict(fontSize=11,leading=15,spaceAfter=6,keepWithNext=True),'cell':dict(fontSize=8.5,leading=12)}.items()}
def para(s,style='body'):
 import re
 t=html.escape(s);t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t);return Paragraph(t,styles[style])
story=[]
for pn,page in enumerate(pages):
 if pn:story.append(PageBreak())
 lines=page.splitlines();i=0
 while i<len(lines):
  line=lines[i].strip();i+=1
  if not line:continue
  if line.startswith('|'):
   rs=[line]
   while i<len(lines) and lines[i].strip().startswith('|'):rs.append(lines[i].strip());i+=1
   rs=[r for r in rs if not set(r)<=set('|- :')]
   cells=[[para(c.strip(),'cell') for c in r.strip('|').split('|')] for r in rs]
   width=503/len(cells[0]);t=Table(cells,colWidths=[width]*len(cells[0]),repeatRows=1)
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eff3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#bdcbd4')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,8)]);continue
  if line.startswith('#'):
   level=len(line)-len(line.lstrip('#'));story.append(para(line.lstrip('# '),'h'+str(level)))
  else:story.append(para(line))
def footer(can,doc):can.setFont('Korean',8);can.drawString(46,815,'망젤이네 · 평일 오전 OD와 대표 버스 노선 연결');can.drawRightString(549,28,str(doc.page))
pdf=OUT/'망젤이네_서울_OD_버스연결_검토.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=46,rightMargin=46,topMargin=43,bottomMargin=43,title='서울 오전 이동 OD와 버스 노선 연결 분석',author='망젤이네').build(story,onFirstPage=footer,onLaterPages=footer)
r=PdfReader(pdf);assert len(r.pages)==4,len(r.pages)
for i,p in enumerate(r.pages):assert f'{i+1} ' in p.extract_text()
print(pdf)
