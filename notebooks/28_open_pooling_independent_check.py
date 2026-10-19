import csv,json
from datetime import datetime
from collections import Counter
from pathlib import Path
from decimal import Decimal
counts={'treatment':Counter(),'all_purposes_same_service':Counter()};totals=Counter();raw=0
with open('data/raw/calltaxi/seoul_calltaxi_2025.csv',encoding='utf-8-sig') as f:
 for r in csv.DictReader(f):
  raw+=1
  if r['출발구'].strip() not in ['중구','성동구','동대문구'] or r['취소일시'].strip() or '예약' in r['이용목적']:continue
  try:a,b,c,d,e=[datetime.fromisoformat(r[k]) for k in ['접수일시','예정일시','배차일시','승차일시','하차일시']]
  except ValueError:continue
  if not(a<=c<=d<=e and 0<=(b-a).total_seconds()<=60):continue
  groups=['all_purposes_same_service']
  if '치료' in r['이용목적'] or '재활' in r['이용목적']:groups+=['treatment']
  for g in groups:
   totals[g]+=1
   if all(r[k].strip() for k in ['출발구','목적구','목적동']):
    slot=a.replace(minute=(a.minute//30)*30,second=0,microsecond=0)
    counts[g][tuple(r[k].strip() for k in ['출발구','목적구','목적동'])+(slot,)]+=1
selected=list(csv.DictReader(open('outputs/tables/open_pooling_verification/service_cooccurrence.csv')))
results={}
for g in counts:
 expected=next(r for r in selected if r['cohort']==g and r['screen']=='origin_district_destination_dong' and r['minutes']=='30' and r['bin_offset_minutes']=='0')
 n=sum(v for v in counts[g].values() if v>=2)
 assert totals[g]==int(expected['records']) and n==int(expected['records_in_2plus'])
 results[g]={'records':totals[g],'cooccurrence_records':n,'matched':True}
assert raw==1729476
# Independent decimal arithmetic checks a consequential vehicle-km threshold.
boundary=(Decimal('1.1')*Decimal('1.77')/Decimal(2))
assert boundary==Decimal('.9735')
results['independent_vkt_threshold_two_onboard_empty77_detour10_car1']=str(boundary)
Path('outputs/tables/open_pooling_verification/independent_check.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(results)
