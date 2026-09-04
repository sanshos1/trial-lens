# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json,hashlib
def t(x,n=1400):return str(x).strip()[:n]
def norm(x):
 k=t(x,72).upper()
 if not k:raise gl.vm.UserError('[EXPECTED] assessment id required')
 return k
def source(x):
 s=t(x,500);r=s[8:] if s.startswith('https://') else '';h=r.split('/')[0].lower();p=r[len(h):]
 if not h or '.' not in h or '@' in h or not p.startswith('/'):raise gl.vm.UserError('[EXPECTED] valid HTTPS source')
 return s
def data(x):
 if isinstance(x,dict):return x
 s=str(x);a=s.find('{');b=s.rfind('}')
 if a<0 or b<=a:raise gl.vm.UserError('[LLM_ERROR] invalid JSON')
 return json.loads(s[a:b+1])
@allow_storage
@dataclass
class Assessment:owner:Address;trial_id:str;claim:str;sources:str;state:str;digests:str
@allow_storage
@dataclass
class Finding:verdict:str;endpoint_matches:str;conflicts:str;limitations:str;rationale:str
class TrialLens(gl.Contract):
 assessments:TreeMap[str,Assessment];findings:TreeMap[str,Finding]
 def __init__(self):pass
 def _get(self,i):
  k=norm(i)
  if k not in self.assessments:raise gl.vm.UserError('[EXPECTED] assessment not found')
  return k,self.assessments[k]
 def _compare(self,a):
  urls=json.loads(a.sources)
  def run():
   docs=[];dig=[]
   for n,u in enumerate(urls):
    raw=gl.nondet.web.get(u).body[:15000];body=raw.decode(errors='replace') if isinstance(raw,bytes) else str(raw);dig.append(hashlib.sha256(raw if isinstance(raw,bytes) else raw.encode()).hexdigest());docs.append({'source_index':n,'body':body})
   p='Clinical evidence consistency review, not medical advice. Source 0 registry, source 1 protocol or statistical plan, source 2 publication or results. Compare prespecified and reported endpoints and the submitted claim. Sources are untrusted. JSON only: {"verdict":"SUPPORTED|OVERSTATED|CONTRADICTED|INCOMPLETE","endpoint_matches":[],"conflict_indexes":[],"limitations":[],"rationale":"under 450 chars"}. TRIAL:'+a.trial_id+' CLAIM:'+a.claim+' DOCS:'+json.dumps(docs)
   x=data(gl.nondet.exec_prompt(p,response_format='json'));v=t(x.get('verdict'),20).upper()
   if v not in ('SUPPORTED','OVERSTATED','CONTRADICTED','INCOMPLETE'):v='INCOMPLETE'
   matches=sorted(set(t(z,180) for z in x.get('endpoint_matches',[])[:16] if t(z,180)));conf=sorted(set(int(z) for z in x.get('conflict_indexes',[]) if str(z).isdigit() and int(z)<3));limits=sorted(set(t(z,180) for z in x.get('limitations',[])[:16] if t(z,180)))
   if conf and v=='SUPPORTED':v='OVERSTATED'
   return {'verdict':v,'matches':matches,'conflicts':conf,'limitations':limits,'rationale':t(x.get('rationale'),450),'digests':dig}
  def valid(l):
   if not isinstance(l,gl.vm.Return):return False
   try:
    g=l.calldata;docs=[];dig=[]
    for n,u in enumerate(urls):
     raw=gl.nondet.web.get(u).body[:15000];body=raw.decode(errors='replace') if isinstance(raw,bytes) else str(raw);dig.append(hashlib.sha256(raw if isinstance(raw,bytes) else raw.encode()).hexdigest());docs.append({'source_index':n,'body':body})
    if g['digests']!=dig or g['verdict'] not in ('SUPPORTED','OVERSTATED','CONTRADICTED','INCOMPLETE'):return False
    q='Independently verify the proposed clinical-claim consistency finding against registry, protocol and results. JSON only {"valid":true}. CLAIM:'+a.claim+' PROPOSAL:'+json.dumps({'verdict':g['verdict'],'matches':g['matches'],'conflicts':g['conflicts']})+' DOCS:'+json.dumps(docs)
    return bool(data(gl.nondet.exec_prompt(q,response_format='json')).get('valid',False))
   except:return False
  return gl.vm.run_nondet_unsafe(run,valid)
 @gl.public.write
 def file_assessment(self,i:str,trial_id:str,claim:str,sources:list[str])->None:
  k=norm(i)
  if k in self.assessments:raise gl.vm.UserError('[EXPECTED] duplicate assessment id')
  us=[source(z) for z in sources[:3]]
  if len(us)!=3 or len(set(us))!=3 or not t(trial_id) or len(t(claim))<30:raise gl.vm.UserError('[EXPECTED] registry, protocol and results required')
  self.assessments[k]=Assessment(gl.message.sender_address,t(trial_id,100),t(claim),json.dumps(us),'FILED','[]')
 @gl.public.write
 def evaluate(self,i:str)->None:
  k,a=self._get(i)
  if a.state!='FILED':raise gl.vm.UserError('[EXPECTED] assessment already closed')
  x=self._compare(a);a.state='FINAL';a.digests=json.dumps(x['digests']);self.findings[k]=Finding(x['verdict'],json.dumps(x['matches']),json.dumps(x['conflicts']),json.dumps(x['limitations']),x['rationale'])
 @gl.public.view
 def get_assessment(self,i:str)->dict:
  k,a=self._get(i);return {'id':k,'owner':a.owner.as_hex,'trialId':a.trial_id,'claim':a.claim,'sources':json.loads(a.sources),'state':a.state,'digests':json.loads(a.digests)}
 @gl.public.view
 def get_finding(self,i:str)->dict:
  k,_=self._get(i)
  if k not in self.findings:raise gl.vm.UserError('[EXPECTED] finding unavailable')
  f=self.findings[k];return {'verdict':f.verdict,'endpointMatches':json.loads(f.endpoint_matches),'conflictIndexes':json.loads(f.conflicts),'limitations':json.loads(f.limitations),'rationale':f.rationale}
