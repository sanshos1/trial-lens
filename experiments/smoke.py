import json,re,time
from pathlib import Path
from genlayer_py import create_client,create_account
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus
ROOT=Path(__file__).parents[1];ENV=(ROOT.parents[3]/'accounts.env').read_text()
def secret(n):return re.search(rf'^ACCOUNT_{n}_GENLAYER_PRIVATE_KEY\s*=\s*"?([^"\r\n]+)',ENV,re.M).group(1).strip()
deploy=json.loads((ROOT/"runs/deployment.json").read_text());contract=deploy['contract']
account=create_account(account_private_key=secret(3));client=create_client(chain=studionet,account=account)
def send(c,fn,args):
 tx=c.write_contract(address=contract,function_name=fn,args=args);print(fn,tx,flush=True)
 c.wait_for_transaction_receipt(transaction_hash=tx,status=TransactionStatus.ACCEPTED,retries=120,interval=10000);info=c.get_transaction(transaction_hash=tx)
 if info.get('status_name')!='ACCEPTED' or not any(r.get('execution_result')=='SUCCESS' for r in info.get('consensus_data',{}).get('leader_receipt',[])):raise RuntimeError({'function':fn,'tx':tx,'status':info.get('status_name'),'execution':info.get('tx_execution_result_name')})
 return tx
def negative(c,fn,args,label):
 try:c.simulate_write_contract(address=contract,function_name=fn,args=args);raise RuntimeError(label+' unexpectedly passed')
 except RuntimeError:raise
 except Exception:print('negative',label,'rejected',flush=True)
assessment='TL-'+str(int(time.time()))
base=f'https://raw.githubusercontent.com/sanshos1/trial-lens/{deploy["evidenceCommit"]}/materials/'
sources=[base+'registry.txt',base+'protocol.txt',base+'results.txt']
args=[assessment,'TL-101','The intervention improves the registered primary mobility endpoint at week 12.',sources]
filed=send(client,'file_assessment',args)
negative(client,'file_assessment',args,'duplicate id')
evaluated=send(client,'evaluate',[assessment])
state=client.read_contract(address=contract,function_name='get_assessment',args=[assessment])
finding=client.read_contract(address=contract,function_name='get_finding',args=[assessment])
assert state['state']=='FINAL' and len(state['digests'])==3 and finding['verdict']=='SUPPORTED'
proof={'assessmentId':assessment,'transactions':{'file':filed,'evaluate':evaluated},'state':state,'finding':finding}
(ROOT/"runs/finding.json").parent.mkdir(parents=True,exist_ok=True)
(ROOT/"runs/finding.json").write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
