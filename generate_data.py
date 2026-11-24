"""Synthetic hotel operations; deterministic seed, no personal information."""
from pathlib import Path
from datetime import date,timedelta
from collections import defaultdict
import csv,random,copy,json
P=Path(__file__).resolve().parent
DESC={
'hotels':{'hotel_id':'INTEGER primary key','hotel_name':'Fictional property name','market':'Business or Leisure positioning','city':'Nigerian city, no actual address','physical_rooms':'Total rooms before out-of-service deductions','base_rate_ngn':'Starting reference nightly rate, NGN excluding taxes'},
'guests':{'guest_id':'INTEGER primary key; synthetic customer, no PII','segment':'Business, Leisure or Group; fixed customer segment','home_region':'Domestic or International; fictional classification'},
'channels':{'channel_id':'INTEGER primary key','channel_name':'Direct, OTA or Corporate agent','commission_rate':'Fraction of realized room revenue charged as commission'},
'inventory':{'inventory_id':'INTEGER primary key','hotel_id':'FK to hotels','stay_date':'ISO date; one hotel-day','rooms_available':'Sellable rooms after out-of-service deductions','out_of_service_rooms':'Physical rooms unavailable for sale'},
'bookings':{'booking_id':'INTEGER key; 150 identical raw copies repeat this key','hotel_id':'FK to hotels; 15 deliberately invalid raw references','guest_id':'FK to guests','channel_id':'FK to channels','booking_date':'ISO reservation creation date; can be in 2023 for early 2024 arrivals','arrival_date':'ISO date, except 200 deliberately DD/MM/YYYY source dates','departure_date':'ISO checkout date, exclusive last night','cancel_date':'ISO cancellation date, blank for completed stays','status':'Completed or Cancelled; 300 raw values padded/lowercase','lead_days':'Days from booking to arrival, 1–180','nights':'Booked length of stay, 1–6 nights; one room per booking','quoted_adr_ngn':'Agreed nightly room rate NGN, constant across this booking; 25 negative source errors','nightly_service_cost_ngn':'Variable servicing cost per occupied night; not full hotel cost','special_requests':'Requested amenity category; 250 missing entries become Unknown','satisfaction_score':'1–5 survey rating, optional and completed-stay only'},
'booking_nights':{'booking_night_id':'INTEGER primary key','booking_id':'FK to bookings','stay_date':'ISO booked night, including cancelled reservations; occupancy depends on booking status'}
}
def generate():
 r=random.Random(161803);out=P/'data/raw';out.mkdir(parents=True,exist_ok=True)
 hotels=[dict(hotel_id=i+1,hotel_name=n,market=m,city=c,physical_rooms=q,base_rate_ngn=p) for i,(n,m,c,q,p) in enumerate([('Harbour House','Business','Lagos',50,55000),('Capital Court','Business','Abuja',60,65000),('Palm Retreat','Leisure','Calabar',40,38000)])]
 guests=[dict(guest_id=i,segment=r.choices(['Business','Leisure','Group'],[.42,.48,.1])[0],home_region=r.choices(['Domestic','International'],[.88,.12])[0]) for i in range(1,8001)]
 channels=[dict(channel_id=i+1,channel_name=n,commission_rate=f) for i,(n,f) in enumerate([('Direct',.02),('OTA',.18),('Corporate agent',.1)])]
 inv=[];capacity={};start=date(2024,1,1);end=date(2025,12,31)
 for k in range(731):
  d=start+timedelta(days=k)
  for h in hotels:
   off=(8 if h['hotel_id']==2 and date(2025,7,1)<=d<=date(2025,8,31) else 0)+(2 if r.random()<.04 else 0)
   inv.append(dict(inventory_id=len(inv)+1,hotel_id=h['hotel_id'],stay_date=d.isoformat(),rooms_available=h['physical_rooms']-off,out_of_service_rooms=off));capacity[h['hotel_id'],d]=h['physical_rooms']-off
 days=[start+timedelta(days=k) for k in range(725)]
 weights=[(1.0+.00035*k)*(1.7 if d.month==12 else 1.2 if d.month in [7,8] else .82 if d.month==2 else 1) for k,d in enumerate(days)]
 candidates=[]
 for k in range(30000):
  arrival=r.choices(days,weights)[0];g=r.choice(guests);hid=r.choices([1,2,3],[.4,.4,.2] if g['segment']=='Business' else [.32,.23,.45])[0];h=hotels[hid-1]
  channel=r.choices([1,2,3],[.22,.15,.63] if g['segment']=='Business' else [.30,.65,.05])[0]
  lead=min(180,max(1,round(r.gammavariate(1.5,22 if channel==2 else 12))))
  bk=arrival-timedelta(days=lead);length=r.choices([1,2,3,4,5,6],[.23,.30,.22,.13,.07,.05])[0]
  cancelled=r.random()<(.10+(.14 if channel==2 else 0)+(.12 if lead>60 else 0))
  cancel=arrival-timedelta(days=r.randint(1,lead)) if cancelled else None
  multiplier=(1.4 if arrival.month==12 else 1)*(1.12 if arrival.weekday() in [4,5] and h['market']=='Leisure' else 1)*(.92 if lead>60 else 1)*(.9 if channel==3 else 1)
  adr=round(h['base_rate_ngn']*(1+.0003*(arrival-start).days)*multiplier*r.uniform(.90,1.10)/100)*100
  cost=round((10000+hid*1500)*(1+.0004*(arrival-start).days),2)
  survey='' if cancelled or r.random()<.32 else max(1,min(5,round(r.gauss(4.2-(.6 if hid==2 and arrival.year==2025 and arrival.month in [7,8] else 0),.8))))
  candidates.append(dict(booking_id=k+1,hotel_id=hid,guest_id=g['guest_id'],channel_id=channel,booking_date=bk.isoformat(),arrival_date=arrival.isoformat(),departure_date=(arrival+timedelta(days=length)).isoformat(),cancel_date=cancel.isoformat() if cancel else '',status='Cancelled' if cancelled else 'Completed',lead_days=lead,nights=length,quoted_adr_ngn=adr,nightly_service_cost_ngn=cost,special_requests=r.choices(['None','Quiet room','Late arrival','High floor'],[.60,.17,.15,.08])[0],satisfaction_score=survey))
 # Accept in booking-date order, holding capacity until cancellation/checkout.
 # Capacity-denied requests are not bookings and are not included in analysis.
 held=defaultdict(list);bookings=[];nightrows=[];declined=0
 for b in sorted(candidates,key=lambda x:(x['booking_date'],x['booking_id'])):
  ds=[date.fromisoformat(b['arrival_date'])+timedelta(days=i) for i in range(b['nights'])];hid=b['hotel_id'];bk=b['booking_date']
  if any(sum(release>bk for release in held[hid,d])>=capacity[hid,d] for d in ds):declined+=1;continue
  b['booking_id']=len(bookings)+1;bookings.append(b)
  release=b['cancel_date'] or b['departure_date']
  for d in ds:
   held[hid,d].append(release);nightrows.append(dict(booking_night_id=len(nightrows)+1,booking_id=b['booking_id'],stay_date=d.isoformat()))
 for b in r.sample(bookings,250):b['special_requests']=''
 for b in r.sample(bookings,300):b['status']=' '+b['status'].lower()+' '
 for b in r.sample(bookings,200):b['arrival_date']=date.fromisoformat(b['arrival_date']).strftime('%d/%m/%Y')
 bad=r.sample(bookings,40)
 for b in bad[:25]:b['quoted_adr_ngn']=-b['quoted_adr_ngn']
 for b in bad[25:]:b['hotel_id']=99999
 raw=bookings+[copy.deepcopy(b) for b in r.sample(bookings,150)]
 rowsmap={'hotels':hotels,'guests':guests,'channels':channels,'inventory':inv,'bookings':raw,'booking_nights':nightrows}
 for name,rows in rowsmap.items():
  with (out/(name+'.csv')).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (P/'reports').mkdir(exist_ok=True)
 (P/'reports/generation.json').write_text(json.dumps({'seed':161803,'candidate_requests':30000,'capacity_declined_requests':declined,'unique_accepted_bookings':len(bookings),'raw_rows':{k:len(v) for k,v in rowsmap.items()}},indent=2))
 doc='# Data dictionary\n\nAll records are synthetic. NGN values exclude tax. Dates are local calendar dates. Blank cells mean NULL, not zero. One booking reserves one room.\n'
 for name,cols in DESC.items():doc+='\n## '+name+'\n\n| Column | Definition |\n|---|---|\n'+''.join(f'| `{k}` | {v} |\n' for k,v in cols.items())
 doc+='''\n## Derived measures\n\n`booking_mart` retains cleaned booking fields and joins hotel_name, market, guest segment, channel_name and commission_rate. `is_cancelled` is 1 for cancellation, else 0. `quoted_value_ngn` = nights × quoted ADR. This is booked value, not earned revenue. `realized_room_revenue_ngn` is zero for cancellations and quoted value for completed stays. `commission_ngn` is realized revenue × commission rate. `service_cost_ngn` is completed room-nights × nightly service cost. `contribution_ngn` = realized revenue − commission − service cost, before fixed costs, tax and capital costs.\n\n`daily_hotel` is a complete inventory grid, including dates with no occupied rooms. It has hotel_id, stay_date, rooms_available, out_of_service_rooms, occupied_rooms (completed booking nights), room_revenue_ngn and contribution_ngn. Zero occupied rooms is valid; bookings with source errors are excluded, so occupancy is based on valid retained records and may undercount true occupancy. ADR = room revenue / occupied room-nights. RevPAR = room revenue / available room-nights. Occupancy = occupied / available room-nights. All aggregate ratios use sums, not averages of hotel percentages.\n\n`quarantine` contains original normalized booking columns plus reason. `bookings_normalized` retains deduplicated and standardized raw records. `booking_nights` is cleaned by excluding children of quarantined bookings. Survey scores are not imputed and response coverage is reported separately. Events after 2025 are not needed: all stays end by 31 December 2025.\n'''
 (P/'DATA_DICTIONARY.md').write_text(doc);print('Accepted bookings:',len(bookings),'night rows:',len(nightrows))
if __name__=='__main__':generate()
