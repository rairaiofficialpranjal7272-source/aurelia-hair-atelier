#!/usr/bin/env python3
"""Aurelia Studio demo booking server. Uses SQLite; set ADMIN_KEY before deployment."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import json, os, re, sqlite3, datetime
BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get('DB_PATH',os.path.join(BASE,'aurelia.sqlite3'))
ADMIN_KEY=os.environ.get('ADMIN_KEY','change-me')
PORT=int(os.environ.get('PORT','4173'))
DEFAULT=['Cut & styling','Signature color','Balayage','Highlights','Extensions','Blowouts','Event styling']
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 with conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,active INTEGER NOT NULL DEFAULT 1)')
  c.execute('''CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, mobile TEXT NOT NULL, email TEXT NOT NULL, service TEXT NOT NULL, date TEXT NOT NULL, time TEXT NOT NULL, message TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Confirmed', created_at TEXT NOT NULL)''')
  for s in DEFAULT: c.execute('INSERT OR IGNORE INTO services(name) VALUES(?)',(s,))
SLOTS=['09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00']
def valid_date(d):
 try:
  x=datetime.date.fromisoformat(d)
  return x>=datetime.date.today() and x.weekday()!=6
 except: return False
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=BASE,**kw)
 def send_json(self,obj,status=200):
  b=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
 def body(self):
  try: return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
  except: return {}
 def do_GET(self):
  p=urlparse(self.path).path
  if p=='/api/services':
   with conn() as c: rows=c.execute('SELECT name FROM services WHERE active=1 ORDER BY id').fetchall()
   return self.send_json({'services':[r['name'] for r in rows]})
  if p=='/api/slots':
   d=urlparse(self.path).query.split('date=',1)[-1]
   if not valid_date(d): return self.send_json({'slots':[]})
   with conn() as c: taken={r['time'] for r in c.execute('SELECT time FROM bookings WHERE date=? AND status != "Cancelled"',(d,))}
   return self.send_json({'slots':[x for x in SLOTS if x not in taken]})
  if p=='/api/admin/bookings':
   if self.headers.get('X-Admin-Key')!=ADMIN_KEY: return self.send_json({'error':'Unauthorized'},401)
   with conn() as c: rows=[dict(r) for r in c.execute('SELECT * FROM bookings ORDER BY date,time')]
   return self.send_json({'bookings':rows})
  if p=='/api/admin/services':
   if self.headers.get('X-Admin-Key')!=ADMIN_KEY: return self.send_json({'error':'Unauthorized'},401)
   with conn() as c: rows=[dict(r) for r in c.execute('SELECT id,name FROM services WHERE active=1 ORDER BY id')]
   return self.send_json({'services':rows})
  if p=='/admin': self.path='/admin.html'
  return super().do_GET()
 def do_POST(self):
  p=urlparse(self.path).path; data=self.body()
  if p=='/api/bookings':
   name=str(data.get('name','')).strip(); mobile=str(data.get('mobile','')).strip(); email=str(data.get('email','')).strip(); service=str(data.get('service','')).strip(); d=str(data.get('date','')).strip(); t=str(data.get('time','')).strip(); msg=str(data.get('message','')).strip()
   errors={}
   if len(name)<2 or len(name)>100: errors['name']='Please enter your full name.'
   if not re.fullmatch(r'\+[1-9]\d{7,14}',re.sub(r'[\s()-]','',mobile)): errors['mobile']='Enter a valid number including country code, e.g. +91 98765 43210.'
   if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]{2,}',email): errors['email']='Enter a valid email address.'
   if not service: errors['service']='Choose a service.'
   if not valid_date(d): errors['date']='Choose a future date. The salon is closed Sundays.'
   if t not in SLOTS: errors['time']='Choose an available appointment time.'
   if len(msg)>1000: errors['message']='Please keep your note under 1,000 characters.'
   if errors: return self.send_json({'error':'Please check the highlighted fields.','fields':errors},422)
   try:
    with conn() as c:
     c.execute('BEGIN IMMEDIATE')
     if not c.execute('SELECT 1 FROM services WHERE name=? AND active=1',(service,)).fetchone(): return self.send_json({'error':'That service is no longer available. Please choose another.'},422)
     if c.execute('SELECT 1 FROM bookings WHERE date=? AND time=? AND status != "Cancelled"',(d,t)).fetchone(): return self.send_json({'error':'That time was just booked. Please select another available slot.'},409)
     c.execute('INSERT INTO bookings(full_name,mobile,email,service,date,time,message,created_at) VALUES(?,?,?,?,?,?,?,?)',(name,re.sub(r'\s+',' ',mobile),email,service,d,t,msg,datetime.datetime.now().isoformat(timespec='seconds')))
     booking_id=c.execute('SELECT last_insert_rowid()').fetchone()[0]
    return self.send_json({'ok':True,'booking_id':booking_id,'message':f'Your appointment request is confirmed for {d} at {t}. We look forward to seeing you.'},201)
   except sqlite3.IntegrityError: return self.send_json({'error':'That time was just booked. Please select another available slot.'},409)
  if p.startswith('/api/admin/'):
   if self.headers.get('X-Admin-Key')!=ADMIN_KEY: return self.send_json({'error':'Unauthorized'},401)
   if p=='/api/admin/services':
    n=str(data.get('name','')).strip()
    if not n or len(n)>80: return self.send_json({'error':'Service name must be 1–80 characters.'},422)
    try:
     with conn() as c: c.execute('INSERT INTO services(name) VALUES(?)',(n,))
     return self.send_json({'ok':True,'name':n},201)
    except sqlite3.IntegrityError: return self.send_json({'error':'That service already exists.'},409)
   if p=='/api/admin/status':
    try:
     with conn() as c: c.execute('UPDATE bookings SET status=? WHERE id=?',(data['status'],int(data['id'])))
     return self.send_json({'ok':True})
    except: return self.send_json({'error':'Could not update booking.'},422)
  return self.send_json({'error':'Not found'},404)
 def do_DELETE(self):
  p=urlparse(self.path).path
  if self.headers.get('X-Admin-Key')!=ADMIN_KEY: return self.send_json({'error':'Unauthorized'},401)
  if p.startswith('/api/admin/services/'):
   try:
    sid=int(p.rsplit('/',1)[1])
    with conn() as c: c.execute('UPDATE services SET active=0 WHERE id=?',(sid,))
    return self.send_json({'ok':True})
   except: return self.send_json({'error':'Could not remove service.'},422)
  return self.send_json({'error':'Not found'},404)
init()
if __name__=='__main__':
 print(f'Aurelia server: http://0.0.0.0:{PORT}  | Admin: /admin  | Set ADMIN_KEY for production')
 ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
