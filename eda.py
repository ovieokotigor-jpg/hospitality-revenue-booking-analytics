"""Exploratory and explanatory analysis; run python analysis/eda.py."""
from pathlib import Path
import sqlite3,json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[1]
NAVY='#24384f';TEAL='#238b83';GOLD='#dca04b';CORAL='#c56b65';BG='#fbf9f4'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'savefig.facecolor':BG,'font.family':'DejaVu Sans','font.size':10,'text.color':NAVY,'axes.labelcolor':NAVY,'axes.spines.top':False,'axes.spines.right':False})
charts=[]
def finish(fig,name,title,note):
 fig.suptitle(title,x=.07,ha='left',fontsize=16,fontweight='bold');fig.text(.07,.025,note,fontsize=9,color='#6b7781');fig.tight_layout(rect=[.02,.07,.98,.91]);fig.savefig(P/'charts'/name,dpi=150);plt.close(fig);charts.append((name,title,note))
def read(n):return pd.read_csv(P/'reports'/f'{n}.csv')
c=sqlite3.connect(P/'hotel.sqlite');daily=pd.read_sql('SELECT * FROM daily_hotel',c);book=pd.read_sql('SELECT * FROM booking_mart',c);c.close()
m=read('monthly');ch=read('channels');lead=read('lead_bands');hm=read('hotel_month');ht=read('hotels');cancel=read('cancellation_timing');bridge=read('revenue_bridge').iloc[0];survey=read('survey')
# Aligned small multiples: no dual-axis scale ambiguity.
fig,ax=plt.subplots(2,1,figsize=(12,6),sharex=True);x=np.arange(len(m));ax[0].plot(x,m.occupancy*100,'o-',color=TEAL);ax[0].set_ylabel('Occupancy (%)');ax[0].set_ylim(0,100)
ax[1].plot(x,m.adr_ngn/1000,color=NAVY,label='ADR');ax[1].plot(x,m.revpar_ngn/1000,color=GOLD,label='RevPAR');ax[1].set_ylabel('NGN thousands');ax[1].legend(frameon=False);ax[1].set_xticks(x[::2],m.month[::2],rotation=30,ha='right')
finish(fig,'01_seasonal_revenue.png','Read occupancy alongside room pricing','Stay-date attribution. Available-room denominator includes refurbishment deductions and all hotel-days.')
# Accounting bridge: cancelled quote value not opportunity cost.
vals=[bridge.quoted_value_ngn,-bridge.cancelled_value_ngn,-bridge.commission_ngn,-bridge.service_cost_ngn];labels=['All booked value','Cancelled quotes','Channel charges','Variable service cost','Contribution'];total=0;fig,ax=plt.subplots(figsize=(11,5))
for i,v in enumerate(vals):
 ax.bar(i,v/1e6,bottom=total/1e6,color=TEAL if v>0 else CORAL,width=.65);total+=v
 ax.text(i,(total if v>0 else total-v)/1e6+15,f'{v/1e6:+,.1f}',ha='center')
assert abs(total-bridge.contribution_ngn)<.01
ax.bar(4,total/1e6,color=NAVY,width=.65);ax.text(4,total/1e6+15,f'{total/1e6:,.1f}',ha='center');ax.set_xticks(range(5),labels,rotation=15,ha='right');ax.set_ylabel('NGN millions')
finish(fig,'02_booking_value_waterfall.png','From booked value to room contribution','Cancelled quotes are not a proven revenue loss. Contribution excludes fixed costs, marketing, tax and capital costs.')
# Channel x lead time heatmap with sample size.
v=lead.pivot(index='channel_name',columns='lead_band',values='cancellation_rate');n=lead.pivot(index='channel_name',columns='lead_band',values='bookings');fig,ax=plt.subplots(figsize=(10,5));im=ax.imshow(v,cmap='YlOrBr',vmin=0,vmax=max(.5,float(v.max().max())),aspect='auto')
for i in range(len(v)):
 for j in range(len(v.columns)):ax.text(j,i,f'{v.iloc[i,j]:.1%}\nn={int(n.iloc[i,j]):,}',ha='center',va='center')
ax.set_xticks(range(len(v.columns)),[s.split(': ')[1] for s in v.columns]);ax.set_yticks(range(len(v)),v.index);ax.set_xlabel('Booking lead time (days)');fig.colorbar(im,ax=ax,label='Cancellation rate')
finish(fig,'03_cancellation_heatmap.png','Cancellation exposure differs across booking groups','Denominator: accepted bookings in each group. Channel and lead time are associated with customer mix.')
# Property commercial positioning; denominator capacity days bubble area.
fig,ax=plt.subplots(figsize=(10,5));ax.scatter(ht.occupancy*100,ht.adr_ngn/1000,s=ht.available_nights/35,c=[TEAL,GOLD,CORAL],alpha=.75,edgecolor='white')
for _,r in ht.iterrows():ax.annotate(r.hotel_name,(r.occupancy*100,r.adr_ngn/1000),xytext=(10,10),textcoords='offset points')
ax.set_xlabel('Occupancy (%)');ax.set_ylabel('ADR (NGN thousands)');ax.margins(.3)
finish(fig,'04_hotel_position_matrix.png','Compare rate and occupancy together','Bubble area = sellable room-nights. Properties serve different markets; this is not a fair causal ranking.')
# When rooms return to market: return notice ECDF.
fig,ax=plt.subplots(figsize=(10,5))
for color,(name,g) in zip([TEAL,NAVY,GOLD],cancel.groupby('channel_name')):
 a=np.sort(g.notice_days);ax.step(a,np.arange(1,len(a)+1)/len(a)*100,where='post',label=f'{name} (n={len(a):,})',color=color,lw=2)
ax.set_xlabel('Days before arrival when cancellation occurs');ax.set_ylabel('Cumulative cancellations (%)');ax.legend(frameon=False)
finish(fig,'05_cancellation_notice_ecdf.png','How much notice does a cancellation provide?','Read the share at seven days to understand late cancellations. Rebooking outcomes are not estimated.')
# Daily variation violin: occupancy uses actual sellable capacity.
fig,ax=plt.subplots(figsize=(10,5));groups=[100*g.occupied_rooms/g.rooms_available for _,g in daily.groupby('hotel_id')];parts=ax.violinplot(groups,showmedians=True,showextrema=False)
for body in parts['bodies']:body.set_facecolor(TEAL);body.set_alpha(.65)
parts['cmedians'].set_color(NAVY);ax.set_xticks([1,2,3],ht.sort_values('hotel_id').hotel_name);ax.set_ylabel('Daily occupancy (%)');ax.set_ylim(0,105)
finish(fig,'06_daily_occupancy_violin.png','Average occupancy conceals daily variability','All 731 days per property are included. High-demand days are capacity-constrained in the simulation.')
# Complete hotel/month heatmap.
v=hm.pivot(index='hotel_id',columns='month',values='occupancy');fig,ax=plt.subplots(figsize=(14,4));im=ax.imshow(v,cmap='YlGnBu',vmin=0,vmax=1,aspect='auto')
for i in range(3):
 for j in range(24):ax.text(j,i,f'{v.iloc[i,j]:.0%}',fontsize=8,ha='center',va='center',color='white' if v.iloc[i,j]>.65 else NAVY)
ax.set_yticks(range(3),ht.sort_values('hotel_id').hotel_name);ax.set_xticks(range(24),v.columns,rotation=60,ha='right');fig.colorbar(im,ax=ax,label='Occupancy fraction')
finish(fig,'07_hotel_calendar.png','Where demand pressure recurs','July–August 2025: Capital Court has fewer available rooms due to a simulated refurbishment.')
# Results: numerical findings generated from SQL outputs.
occ=daily.occupied_rooms.sum()/daily.rooms_available.sum();adr=daily.room_revenue_ngn.sum()/daily.occupied_rooms.sum();revpar=daily.room_revenue_ngn.sum()/daily.rooms_available.sum();cr=book.is_cancelled.mean();worst=ch.loc[ch.cancellation_rate.idxmax()];late=(cancel.notice_days<=7).mean()
findings=f'''- Occupancy: **{occ:.1%}** across all sellable room-nights.
- Average daily rate (ADR): **NGN {adr:,.0f}** per occupied room-night.
- Revenue per available room (RevPAR): **NGN {revpar:,.0f}**.
- Cancellation rate: **{cr:.1%}** of retained accepted bookings. **{worst.channel_name}** has the highest channel rate at **{worst.cancellation_rate:.1%}**.
- **{late:.1%}** of cancellations occurred within seven days of arrival.
- Realized room revenue: **NGN {bridge.room_revenue_ngn:,.0f}**; room contribution after channel charges and variable service costs: **NGN {bridge.contribution_ngn:,.0f}**. This is not net profit.
'''
au=json.loads((P/'reports/validation.json').read_text());gen=json.loads((P/'reports/generation.json').read_text());counts='\n'.join(f'| {k} | {v:,} |' for k,v in gen['raw_rows'].items())
md=f'''# Hotel Revenue and Cancellation Analytics

**SQL · Python · Synthetic hospitality data · Explanatory analysis**

## Business objective
A fictional three-property hotel group wants to understand occupancy, room pricing and cancellation exposure. The analysis supports revenue managers deciding where to investigate booking policies, distribution channels and availability constraints.

The central question is: **how do booking mix, lead time and available inventory relate to realized room revenue and contribution?** This is a new hospitality project, separate from the earlier fleet, retail and solar examples.

## Executive findings
{findings}
## Dataset and scope
All data is synthetic, with seed 161803. Stay dates cover 1 January 2024–31 December 2025. Bookings may be made in 2023 for 2024 stays. All outcomes are mature; no future unresolved reservations. One booking reserves one room for 1–6 nights. Rates and costs are fictional NGN excluding taxes, not market benchmarks. No real personal information is included.

| Raw CSV | Rows |
|---|---:|
{counts}

The generator proposes 30,000 requests and accepts **{gen['unique_accepted_bookings']:,}** within capacity. **{gen['capacity_declined_requests']:,}** capacity-denied candidates are not reservation records. This is an accepted-bookings dataset, not a complete demand funnel. See [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for every column and unit.

## Relationships and grain
Hotels have many daily inventory records and bookings. Guests and channels each have many bookings. Bookings have many booking_nights. Each booked night is linked to daily inventory through the booking's hotel and stay_date. Cancelled bookings keep their scheduled nights but do not occupy inventory in realized reporting.

```mermaid
erDiagram
    HOTELS ||--o{{ INVENTORY : supplies
    HOTELS ||--o{{ BOOKINGS : receives
    GUESTS ||--o{{ BOOKINGS : makes
    CHANNELS ||--o{{ BOOKINGS : sources
    BOOKINGS ||--|{{ BOOKING_NIGHTS : schedules
```

## Simulation design
- Three different hotel capacities, prices and business/leisure market positions.
- Unequal segments and channel preferences, right-skewed lead times, variable lengths of stay and repeat guests.
- December peaks, smaller summer effects, scenario price growth and leisure weekend pricing.
- OTA and long-lead reservations have higher simulated cancellation probability. This is an injected assumption, not a real industry claim.
- Capacity is checked in booking-date order. Rooms stay reserved until cancellation or checkout. Cancellations are processed before new bookings on the same date, since intraday timestamps are not modeled.
- Known out-of-service inventory reduces sellable capacity, including a refurbishment at Capital Court in July–August 2025.
- Accepted bookings are capacity-constrained without overbooking. Cancellation timing can release rooms for later requests.
- Some completed guests provide survey ratings; optional scores are never zero-filled.
- Raw quality issues: 150 exact duplicate bookings, 200 mixed date formats, 300 padded/lowercase statuses, 250 missing request labels, 25 negative rates and 15 invalid hotel references. Survey missingness and cancellation-related nulls are separate from errors.

## Cleaning and preparation
Python loads raw CSVs as text after numeric-syntax validation. SQLite scripts normalize dates and status, preserve optional NULLs, label missing request categories Unknown, remove identical duplicate copies and quarantine invalid rates/references. All nightly children of quarantined bookings are excluded. Raw data remains inspectable.

**Audit:** {au['raw_bookings']:,} raw booking rows − 150 duplicate copies − 40 quarantined bookings = **{au['clean_counts']['bookings']:,}** clean bookings. The complete inventory grid retains all **2,193 hotel-days**, including days with zero occupancy. Excluding invalid bookings can understate true occupancy/revenue; quarantine is disclosed rather than silently repaired.

`sql/01_clean_transform.sql` builds booking_mart and daily_hotel. Nightly revenue is aggregated before joining inventory so available rooms are not multiplied by booking rows. `sql/02_analysis.sql` contains eight named analyses. `sql/03_validation.sql` checks relationships, date order, lead time, nightly counts, room capacity and agreement between booking and daily economic totals. Unique indexes protect primary and composite keys.

## KPI definitions
| KPI | Definition |
|---|---|
| Occupancy | Completed occupied room-nights / sellable available room-nights |
| ADR | Realized room revenue / completed occupied room-nights |
| RevPAR | Realized room revenue / sellable available room-nights |
| Cancellation rate | Cancelled accepted bookings / all accepted bookings retained after cleaning |
| Quoted value | Booked nights × agreed ADR, including later cancellations |
| Room contribution | Realized room revenue − channel charges − variable room servicing costs |
| Survey response rate | Completed bookings with score / completed bookings |

At aggregate level RevPAR = ADR × occupancy. Ratios use sums, never averages of hotel rates. Revenue is attributed to each occupied stay date, not booking or checkout date. All cancellations are free in this simplified scenario: no deposits, penalties or cancellation commission. Direct channel has a 2% assumed processing/distribution charge; it is not cost-free. Contribution excludes salaries, rent, marketing, tax, capital expenditure and other fixed costs.

The booked-value waterfall is an accounting reconciliation. Cancelled quoted value is **not** a measured opportunity loss: rooms may be resold and accepted booking histories can include successive reservations for the same inventory.

## Explanatory charts
'''
for name,title,note in charts:md+=f'\n### {title}\n![{title}](charts/{name})\n{note}\n'
md+='''
## Recommended actions
1. Investigate high-cancellation channel/lead-time groups, controlling for segment and property before changing policy.
2. Review late-cancellation exposure and track whether released rooms are resold; add rebooking linkage before estimating lost revenue.
3. Compare contribution per occupied and available room, not only gross ADR. Add acquisition costs before claiming direct-channel ROI.
4. Evaluate refurbishment with the reduced available-room denominator and guest feedback response coverage.
5. Test policy changes with a credible experiment; avoid interpreting simulated observational patterns as causal evidence.

## Reproduction
Extract the ZIP first. Python 3.10+ is required; SQLite ships with Python. Open a terminal in the folder containing requirements.txt:

```bash
python -m pip install -r requirements.txt
python pipeline.py
```

The pipeline also runs `dashboard/dashboard.py` to generate two 16:9 dashboard pages in PNG and PDF. To rebuild only the dashboard after preparing the data, run `python dashboard/dashboard.py`. No HTML source is included. Python handles generation, loading, analysis, charting and dashboard export; SQL handles relational cleaning and analytical queries.

On Windows, double-click RUN_WINDOWS.bat or use py instead of python. Existing raw files are reused. Run `python generate_data.py` to regenerate them explicitly. Run `python analysis/eda.py` to rebuild charts, README and findings from the prepared database and report CSVs. Generated outputs are overwritten; preserve personal README edits separately.

## Repository contents
| Path | Purpose |
|---|---|
| data/raw/ | Six source CSVs |
| data/clean/ | Clean tables, quarantine and analytical tables |
| sql/ | Schema, cleaning/transformation, analytical queries and validation |
| analysis/eda.py | Complete Python EDA and chart code |
| analysis/findings.md | Executive findings |
| charts/ | Seven explanatory PNG charts |
| reports/ | SQL outputs, generation and validation reports |
| dashboard/dashboard.py | Python dashboard builder with PNG and PDF exports |
| dashboard/dashboard.png | Revenue dashboard preview |
| dashboard/revenue_dashboard.png | Revenue performance page |
| dashboard/booking_risk_dashboard.png | Booking risk and channel page |
| dashboard/dashboard.pdf | Combined two-page dashboard PDF |
| hotel.sqlite | Ready-to-query SQLite database |
| DATA_DICTIONARY.md | Column definitions, units and measures |

## Dashboard design
Two static 16:9 pages use a navy-and-white layout inspired by the supplied visual references: sidebar page labels, KPI cards with monthly sparklines, comparative bars, doughnut charts and scorecards. All KPIs cover 2024–2025. Revenue sparklines use stay month; booking-risk sparklines use arrival month. Each sparkline has its own scale and is for trend shape only. The revenue growth comparison is 2025 versus 2024. Sidebar labels and scope labels are not interactive controls. Build both pages with `python dashboard/dashboard.py`.

![Revenue dashboard](dashboard/revenue_dashboard.png)
![Booking risk dashboard](dashboard/booking_risk_dashboard.png)

## GitHub
Repository name: `hotel-revenue-cancellation-analysis`

Description: End-to-end hospitality analytics using synthetic hotel bookings, SQL and Python to explore occupancy, cancellations, room revenue and contribution.

Initial commit: `Add hotel revenue and cancellation analytics project`

Upload the extracted folder's contents with README.md at the root; preserve chart paths. Include datasets, code, charts and reports. Exclude .venv, __pycache__ and the ZIP archive.

## Limitations
Synthetic assumptions are not calibrated to actual hotel data. All bookings reserve one room; no room types, upgrades, no-shows, partial stays, tax, food/beverage, deposits, penalties or detailed cash ledgers are modeled. Each booking's ADR is constant over its stay. Inventory closures are known at booking time. Capacity-denied candidates are excluded, so observed booking patterns cannot estimate total demand. Quarantined bookings cause small coverage losses. Guest segments are stable; surveys are optional and not automatically representative. No statistical significance or causal claims are made.

## Skills demonstrated
Relational modeling, temporal data generation, capacity constraints, SQL cleaning, raw-to-clean reconciliation, safe joins, denominator design, commercial KPI definitions, distribution analysis, reproducibility and visual storytelling.
'''
(P/'README.md').write_text(md);(P/'analysis/findings.md').write_text('# Executive findings\n\n'+findings)
(P/'reports/environment.json').write_text(json.dumps({'python':__import__('sys').version,'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__},indent=2))
print(findings);print('Generated seven charts, README and findings.')
