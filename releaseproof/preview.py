"""Stateless WSGI verification preview. No DB writes, model calls or acceptance."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from .core import MAX_SOURCE, verify
ROOT=Path(__file__).resolve().parents[1]
CONFIG={'mode':'hosted-preview','persistent_evidence':False,'acceptance_enabled':False,'live_providers':False}
SECURITY=[('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),
          ('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")]

def app(environ,start_response):
    def reply(code,data,kind='application/json'):
        raw=json.dumps(data).encode() if kind=='application/json' else data
        start_response(code,[('Content-Type',kind),('Content-Length',str(len(raw))),*SECURITY])
        return [raw]
    method=environ.get('REQUEST_METHOD','GET')
    path=environ.get('PATH_INFO','/')
    if method=='GET':
        if path in ('/health','/api/config'):
            return reply('200 OK',{'status':'verification-only',**CONFIG})
        if path=='/api/examples':
            return reply('200 OK',{p.stem:p.read_text() for p in sorted((ROOT/'examples').glob('*.py'))})
        routes={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if path in routes:
            file,kind=routes[path]
            return reply('200 OK',(ROOT/'web'/file).read_bytes(),kind)
        if path.startswith('/api/runs/'):
            return reply('503 Service Unavailable',{'error':'Persistent evidence storage is not connected.','gate':'blocked'})
        return reply('404 Not Found',{'error':'Not found.'})
    if method!='POST':return reply('405 Method Not Allowed',{'error':'Method not allowed.'})
    origin=environ.get('HTTP_ORIGIN')
    if origin:
        parsed=urlsplit(origin)
        host=environ.get('HTTP_HOST','')
        local=host.startswith(('127.0.0.1:','localhost:'))
        if parsed.netloc!=host or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.scheme not in (('https','http') if local else ('https',)):
            return reply('403 Forbidden',{'error':'Cross-origin request refused.'})
    if path=='/api/accept':
        return reply('503 Service Unavailable',{'error':'Acceptance is disabled until durable evidence storage is connected.','gate':'blocked'})
    if path!='/api/verify':return reply('404 Not Found',{'error':'Not found.'})
    if environ.get('CONTENT_TYPE','').split(';')[0]!='application/json':
        return reply('415 Unsupported Media Type',{'error':'JSON required.'})
    try:
        size=int(environ.get('CONTENT_LENGTH','0'))
        if not 0<size<=20000:return reply('413 Content Too Large',{'error':'Request too large or empty.'})
        raw=environ['wsgi.input'].read(size)
        if len(raw)!=size:raise ValueError()
        data=json.loads(raw)
        if not isinstance(data,dict) or set(data)!={'source'}:raise ValueError()
        source=data['source']
        if not isinstance(source,str) or len(source.encode())>MAX_SOURCE:raise ValueError()
        report=verify(source)
        report['storage']='not-persisted'
        report['acceptance_enabled']=False
        if report['status']=='pass':
            report['reason']='All 40 bounded checks passed. Evidence is not persisted; acceptance remains disabled.'
        return reply('200 OK',report)
    except (ValueError,UnicodeError,RecursionError):
        return reply('400 Bad Request',{'error':'Invalid verification request.','gate':'blocked'})
