from conftest import CONTRACT
URLS=['https://registry.example/trial/T1','https://protocol.example/T1','https://journal.example/T1']
def mocks(vm):
 vm.strict_mocks=True;vm.check_pickling=True
 vm.mock_web(r'registry\.example',{'status':200,'body':'Primary endpoint: change in score at week 12.'});vm.mock_web(r'protocol\.example',{'status':200,'body':'Prespecified endpoint is score change at week 12.'});vm.mock_web(r'journal\.example',{'status':200,'body':'Week 12 score improved; secondary endpoint was not significant.'})
 vm.mock_llm(r'.*Clinical evidence consistency review.*','{"verdict":"SUPPORTED","endpoint_matches":["week 12 score change"],"conflict_indexes":[],"limitations":["secondary endpoint not significant"],"rationale":"Primary endpoint aligns."}')
def test_three_source_assessment(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);mocks(direct_vm);c.file_assessment(' t-1 ','TRIAL-T1','The intervention improves the registered primary endpoint at week 12.',URLS);c.evaluate('T-1');a=c.get_assessment(' t-1 ')
 assert a['state']=='FINAL' and len(a['digests'])==3 and c.get_finding('T-1')['verdict']=='SUPPORTED'
def test_duplicate_and_exact_three_sources(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);c.file_assessment('T-2','TRIAL-T1','The intervention improves the registered primary endpoint at week 12.',URLS)
 with direct_vm.expect_revert('duplicate assessment id'):c.file_assessment(' t-2 ','TRIAL-T1','The intervention improves the registered primary endpoint at week 12.',URLS)
 with direct_vm.expect_revert('registry, protocol and results'):c.file_assessment('T-3','TRIAL-T1','The intervention improves the registered primary endpoint at week 12.',URLS[:2])
def test_forged_endpoint_match_fails(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);mocks(direct_vm);c.file_assessment('T-4','TRIAL-T1','The intervention improves the registered primary endpoint at week 12.',URLS);result=c._compare(c.assessments['T-4']);direct_vm.mock_llm(r'.*Independently verify.*','{"valid":true}');assert direct_vm.run_validator(leader_result=result) is True;forged=dict(result);forged['digests']=list(reversed(result['digests']))
 assert direct_vm.run_validator(leader_result=forged) is False
