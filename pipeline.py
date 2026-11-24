from pathlib import Path
import sqlite3,csv,re,json,subprocess,sys
P=Path(__file__).resolve().parent
def queries(f):
 x=re.split(r'-- name: (\w+)\n',f.read_text());return zip(x[1::2],x[2::2])
def main():
 for d in ['reports','data/clean','charts','dashboard','analysis']:(P/d).mkdir(parents=True,exist_ok=True)
 if not (P/'data/raw/bookings.csv').exists():
  from generate_data import generate
  generate()
 c=sqlite3.connect(P/'hotel.sqlite');schema=[]
 numeric={'physical_rooms','commission_rate','rooms_available','out_of_service_rooms','lead_days','nights','satisfaction_score'}
 for f in sorted((P/'data/raw').glob('*.csv')):
  with f.open() as inp:rows=list(csv.DictReader(inp))
  cols=list(rows[0]);name='raw_'+f.stem
  for row in rows:
   for k,v in row.items():
    if (k.endswith('_id') or k.endswith('_ngn') or k in numeric) and v!='' and not re.fullmatch(r'-?\d+(\.\d+)?',v):raise ValueError(f'Invalid number {name}.{k}')
  c.execute('DROP TABLE IF EXISTS '+name);ddl='CREATE TABLE '+name+' ('+','.join(x+' TEXT' for x in cols)+');';schema.append(ddl);c.execute(ddl)
  c.executemany('INSERT INTO '+name+' VALUES ('+','.join('?' for x in cols)+')',[list(x.values()) for x in rows]);c.commit()
 (P/'sql/00_schema.sql').write_text('\n'.join(schema));c.executescript((P/'sql/01_clean_transform.sql').read_text())
 checks={n:c.execute(q).fetchone()[0] for n,q in queries(P/'sql/03_validation.sql')};assert not any(checks.values()),checks
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 def export(q,path):
  cur=c.execute(q)
  with path.open('w',newline='') as f:w=csv.writer(f);w.writerow([x[0] for x in cur.description]);w.writerows(cur.fetchall())
 counts={}
 for n in ['hotels','guests','channels','inventory','bookings','booking_nights','quarantine','booking_mart','daily_hotel']:
  counts[n]=c.execute('SELECT COUNT(*) FROM '+n).fetchone()[0];export('SELECT * FROM '+n,P/'data/clean'/f'{n}.csv')
 raw=c.execute('SELECT COUNT(*) FROM raw_bookings').fetchone()[0];assert raw==counts['bookings']+counts['quarantine']+150;assert counts['quarantine']==40
 for n,q in queries(P/'sql/02_analysis.sql'):export(q,P/'reports'/f'{n}.csv')
 audit={'raw_bookings':raw,'duplicates_removed':150,'clean_counts':counts,'validation_failures':checks};(P/'reports/validation.json').write_text(json.dumps(audit,indent=2));c.close();print(json.dumps(audit,indent=2))
 subprocess.run([sys.executable,str(P/'analysis/eda.py')],check=True)
 subprocess.run([sys.executable,str(P/'dashboard/dashboard.py')],check=True)
if __name__=='__main__':main()
