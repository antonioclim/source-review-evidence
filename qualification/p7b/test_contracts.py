"""P7B supplementary contract tests: valid and rejected inputs.
White-box case design from declared contracts; original suites are unchanged.
This is a separate cohort, not an external-use prevalence study.
"""
from __future__ import annotations
import copy,json,math,sys,tempfile,unittest
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch
import codeprobe_measurement_kernel as k
import codeprobe_review_contract as r
import codeprobe_interpretation as it
import codeprobe_numeric_policy as n
import codeprobe_evidence_gates as g
import codeprobe_s01_observation_adapter as ad
ROOT=Path(k.__file__).resolve().parents[1]


def observation():
    return {'observation_id':'obs.1','spec_version':'1','entity':{'kind':'file','identity':'x.py'},'attribute':'count','value':1,'unit':'count','measurement_scale':'ratio','applicability':{'status':'observed','reason':''},'scope_qualification':'One source file','source_evidence':[{'evidence_id':'ev.1','source_id':'x.py','start':1,'end':1,'evidence_kind':'line_span','coordinate_system':'physical_line_numbers_inclusive'}],'instrumentation':{'adapter':'test-contract','runtime':'python'},'metamorphic_contract':'Whitespace preserves count','fingerprint':'0'*64}

def dimension():
    return {'dimension_id':'dim.1','spec_version':'1','status':'evidence_available','observation_refs':['obs.1'],'interpretation':'Count is descriptive','limitations':['One file']}

def action():
    return {'action_id':'act.1','dimension_id':'dim.1','observation_refs':['obs.1'],'policy_rule_id':'rule.1','review_question':'Can this function be simplified?','suggested_change':'Inspect function','rationale':'Local complexity','expected_benefit':'Readable source','trade_offs':['Manual effort'],'source_evidence_refs':['ev.1'],'applicability':'supported','reversible':True}

def report():
    return {'schema':r.REPORT_SCHEMA,'report_kind':'file','software':{'name':'CodeProbe','version':'test','contract_version':r.CONTRACT_VERSION},'input':{'kind':'file','fingerprint':'1'*64,'provenance':'Generated contract fixture'},'specification_catalogue':{'schema':'codeprobe-observation-catalogue/v1','version':'1','digest':'2'*64},'policy_catalogue':{'schema':r.POLICY_CATALOGUE_SCHEMA,'version':'1','digest':'3'*64,'rule_ids':['rule.1']},'observations':[observation()],'review_evidence':{'profile_schema':r.EVIDENCE_PROFILE_SCHEMA,'dimensions':[dimension()],'composition_rule':'vector_only_non_compensatory'},'feedback_actions':[action()],'non_inferences':list(r.REQUIRED_NON_INFERENCES),'legacy_compatibility':None,'deterministic_digest':'0'*64}

def setpath(obj,path,value):
    cur=obj
    for part in path[:-1]:cur=cur[part]
    cur[path[-1]]=value
    return obj

class ReviewContracts(unittest.TestCase):
    def reject(self,func,base,cases):
        for path,value in cases:
            with self.subTest(path=path,value=repr(value)):
                altered=setpath(copy.deepcopy(base),path,value)
                with self.assertRaises((ValueError,TypeError)):func(altered)
    def test_valid_report_and_independent_digest(self):
        for kind in ('file','project'):
            v=report();v['report_kind']=kind;v['input']['kind']=kind
            x=r.finalise_report(v);r.validate_review_report(x)
            import hashlib
            self.assertEqual(x['deterministic_digest'],hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
            x['input']['provenance']='changed'
            with self.assertRaisesRegex(ValueError,'digest'):r.validate_review_report(x)
            r.validate_review_report(x,check_digest=False)
    def test_every_required_report_field(self):
        for key in sorted(r.TOP_LEVEL_FIELDS-{'legacy_compatibility'}):
            x=report();del x[key]
            with self.subTest(key=key),self.assertRaises(ValueError):r.validate_review_report(x,check_digest=False)
        x=report();x['unexpected']=0
        with self.assertRaises(ValueError):r.validate_review_report(x,check_digest=False)
        with self.assertRaises(ValueError):r.validate_review_report([])
    def test_report_metadata_contracts(self):
        cases=[(('schema',),'bad'),(('report_kind',),'unknown'),(('software',),[]),(('software','name'),'Other'),(('software','contract_version'),'0'),(('software','version'),''),(('input','kind'),'unknown'),(('input','fingerprint'),'x'),(('input','provenance'),''),(('specification_catalogue','schema'),'bad'),(('specification_catalogue','version'),''),(('specification_catalogue','digest'),'X'*64),(('policy_catalogue','schema'),'bad'),(('policy_catalogue','rule_ids'),[]),(('policy_catalogue','rule_ids'),['A!']),(('observations',),[]),(('review_evidence',),{}),(('review_evidence','profile_schema'),'bad'),(('review_evidence','composition_rule'),'sum'),(('review_evidence','dimensions'),[]),(('feedback_actions',),{}),(('non_inferences',),[])]
        self.reject(lambda x:r.validate_review_report(x,check_digest=False),report(),cases)
    def test_duplicates_unknown_references(self):
        cases=[]
        for path in [('observations',),('review_evidence','dimensions'),('feedback_actions',)]:
            x=report();cur=x
            for key in path:cur=cur[key]
            cur.append(copy.deepcopy(cur[0]));cases.append(x)
        x=report();ob=observation();ob['observation_id']='obs.2';x['observations'].append(ob);cases.append(x)
        for x in cases:
            with self.subTest(x=x),self.assertRaises(ValueError):r.validate_review_report(x,check_digest=False)
    def test_observation_required_and_extra_fields(self):
        for key in r.OBSERVATION_FIELDS:
            x=observation();del x[key]
            with self.subTest(key=key),self.assertRaises(ValueError):r._validate_observation(x,0)
        x=observation();x['extra']=1
        with self.assertRaises(ValueError):r._validate_observation(x,0)
        with self.assertRaises(ValueError):r._validate_observation(None,0)
    def test_observation_scalars_shapes(self):
        cases=[(('observation_id',),'UpperCase'),(('spec_version',),''),(('attribute',),''),(('unit',),''),(('measurement_scale',),'bad'),(('value',),{}),(('value',),float('nan')),(('value',),None),(('applicability',),{}),(('applicability','status'),'missing'),(('applicability','reason'),'unexpected'),(('scope_qualification',),''),(('source_evidence',),[]),(('source_evidence',),{}),(('source_evidence',0),{}),(('source_evidence',0,'evidence_id'),'Bad!'),(('source_evidence',0,'source_id'),''),(('source_evidence',0,'evidence_kind'),'bad'),(('source_evidence',0,'coordinate_system'),'bad'),(('source_evidence',0,'start'),0),(('source_evidence',0,'start'),True),(('source_evidence',0,'end'),False),(('source_evidence',0,'end'),0),(('entity',),{}),(('entity','kind'),'unknown'),(('entity','identity'),''),(('instrumentation',),{}),(('instrumentation','adapter'),''),(('instrumentation','runtime'),''),(('metamorphic_contract',),''),(('fingerprint',),'x')]
        self.reject(lambda x:r._validate_observation(x,0),observation(),cases)
    def test_observation_states_and_evidence_kinds(self):
        for state in r.APPLICABILITY_STATES-{'observed'}:
            x=observation();x.update(value=None,applicability={'status':state,'reason':'Explicit reason'})
            self.assertEqual(r._validate_observation(x,0)[0],'obs.1')
            for field,val in [('value',0),('reason','')]:
                y=copy.deepcopy(x)
                if field=='value':y[field]=val
                else:y['applicability'][field]=val
                with self.assertRaises(ValueError):r._validate_observation(y,0)
        for kind,coordinate in r.SOURCE_COORDINATE_SYSTEMS.items():
            x=observation();x['source_evidence'][0].update(evidence_kind=kind,coordinate_system=coordinate,start=1 if kind=='line_span' else 0)
            r._validate_observation(x,0)
        x=observation();x['source_evidence'].append(copy.deepcopy(x['source_evidence'][0]))
        with self.assertRaises(ValueError):r._validate_observation(x,0)
        for value in [0,False,'category',1.25]:
            x=observation();x['value']=value;r._validate_observation(x,0)
    def test_dimension_contract(self):
        for key in r.DIMENSION_FIELDS:
            x=dimension();del x[key]
            with self.assertRaises(ValueError):r._validate_dimension(x,0,{'obs.1'})
        self.reject(lambda x:r._validate_dimension(x,0,{'obs.1'}),dimension(),[(('status',),'bad'),(('observation_refs',),['unknown']),(('observation_refs',),[]),(('status',),'not_applicable'),(('limitations',),[1])])
        x=dimension();x.update(status='not_applicable',observation_refs=[]);r._validate_dimension(x,0,set())
        x['extra']=0
        with self.assertRaises(ValueError):r._validate_dimension(x,0,set())
    def test_action_required_fields(self):
        for key in r.ACTION_FIELDS:
            x=action();del x[key]
            with self.assertRaises(ValueError):r.validate_feedback_action(x)
        x=action();x['extra']=1
        with self.assertRaises(ValueError):r.validate_feedback_action(x)
    def test_action_references_and_qualifiers(self):
        kwargs={'observation_ids':{'obs.1'},'dimension_observation_refs':{'dim.1':{'obs.1'}},'observation_evidence_refs':{'obs.1':{'ev.1'}},'policy_rule_ids':{'rule.1'}}
        r.validate_feedback_action(action(),**kwargs);r.validate_feedback_action(action())
        cases=[(('observation_refs',),['missing']),(('dimension_id',),'missing'),(('policy_rule_id',),'missing'),(('source_evidence_refs',),['other']),(('review_question',),'No question'),(('applicability',),'bad'),(('reversible',),False),(('reversible',),1),(('trade_offs',),['x','x'])]
        self.reject(lambda x:r.validate_feedback_action(x,**kwargs),action(),cases)
        with self.assertRaises(ValueError):r.validate_feedback_action(action(),dimension_observation_refs={'dim.1':set()})
        for phrase in r.FORBIDDEN_ACTION_PHRASES:
            x=action();x['rationale']=phrase
            with self.assertRaises(ValueError):r.validate_feedback_action(x)
    def test_json_finiteness_duplicates_and_root(self):
        for text in ['[]','null','42','{','{"a":1,"a":2}','{"x":NaN}','{"x":1e999}','{"x":Infinity}']:
            with self.subTest(text=text),self.assertRaises(ValueError):r.strict_json_loads(text)
        with self.assertRaises(TypeError):r.strict_json_loads(b'{}')
        self.assertEqual(r.strict_json_loads('{"x":1.25}'),{'x':1.25})
        for val in [float('inf'),[float('nan')],{'x':float('-inf')}]:
            with self.assertRaises(ValueError):r.canonical_json(val)
        self.assertEqual(json.loads(r.canonical_json({'list':[True,1,1.5,None]})),{'list':[True,1,1.5,None]})
    def test_prohibition_and_normalisation(self):
        for key in ['AIProbability','humanLikelihood','misconductVerdict','sanctionTrigger','independent_work_flag']:
            with self.assertRaises(ValueError):r.assert_no_forbidden_identifiers([{'inside':{key:0}}])
        for text in ['detects ai-generated code','probability of authorship','proves misconduct','sanction required','manual review required','source is human-written','ai-generated source']:
            with self.assertRaises(ValueError):r.assert_no_prohibited_affirmative_claims({'x':[text]})
        r.assert_no_prohibited_affirmative_claims(list(r.REQUIRED_NON_INFERENCES))
        for x in ['human','hybrid',{'source_origin':'unknown'},{'creator_class':'unknown'}]:
            with self.assertRaises(ValueError):r.assert_no_provenance_policy_labels(x)
        r.assert_no_provenance_policy_labels({'metric':'count'})
    def test_legacy_migration(self):
        cases=[{'schema_version':'2','metrics':{'n':1,'overall_score':99,'labels':['human','useful']}},{'report_schema_version':'2','report_kind':'project','files':[]},{'project_schema_version':'2','project':{}},{'schema':'old','analysis_kind':'file','x':[None,True,1.25]},{'version':'old'},{'language':'python'}]
        for x in cases:
            e=r.migrate_legacy_report(x);self.assertTrue(e['non_equivalent']);self.assertEqual(e['source_digest'],r.digest_json(x))
        with self.assertRaises(ValueError):r.migrate_legacy_report({})
        with self.assertRaises(ValueError):r.migrate_legacy_report({'metrics':[float('nan')]})
        with self.assertRaises(ValueError):r.migrate_legacy_report(cases[0],policy_profile={'source_origin':'AI'})
        r.migrate_legacy_report(cases[0],policy_profile={'policy':'descriptive'})
        with self.assertRaises(ValueError):r._collect_legacy_values({'items':[1,2]},maximum=1)
        values,discarded=r._collect_legacy_values(cases[0]);self.assertTrue(any('overall_score' in d for d in discarded));self.assertFalse(any(v['value']=='human' for v in values))
    def test_legacy_annotation_report(self):
        x=report();x['legacy_compatibility']={'source_schema':'old','source_digest':'a'*64,'source_digest_scope':'canonical_json','non_equivalent':True,'discarded_fields':['score']}
        r.validate_review_report(x,check_digest=False)
        for field,value in [('non_equivalent',False),('source_digest_scope','raw'),('source_schema',''),('source_digest','z'),('discarded_fields',[1])]:
            y=copy.deepcopy(x);y['legacy_compatibility'][field]=value
            with self.assertRaises(ValueError):r.validate_review_report(y,check_digest=False)
        x['legacy_compatibility']['extra']=0
        with self.assertRaises(ValueError):r.validate_review_report(x,check_digest=False)

class KernelContracts(unittest.TestCase):
    def test_generated_language_families(self):
        cases=[(b'', 'text'),(b'\xef\xbb\xbfhello\r\nworld\r','text'),(b'# Heading\n\ntext\n-----\n~~~py\n## hidden\n~~~\n- item\n[x](here)\n','markdown'),(b'## Jump\n```\nunclosed\n','markdown'),(b'def f(:','python'),(b'# comment\nx="doc"\n','python'),(b'async def f(x:int=1)->int:\n "doc"\n for y in [1,2]:\n  if y: continue\n else: x=0\n return x\n','python'),(b'class A:\n def f(self):\n  try: x=1\n  except ValueError: x=2\n  return [i for i in range(3) if i]\n','python')]
        for raw,lang in cases:
            with self.subTest(raw=raw):
                v=k.measure_bytes(raw,language=lang,path='fixture');k.validate_kernel_result(v)
                self.assertEqual(v,k.measure_bytes(raw,language=lang,path='fixture'))
    def test_intake_rejections_and_files(self):
        for value in [None,'text',42]:
            with self.assertRaises(TypeError):k.intake_from_bytes(value)
        for budget in [0,-1,True,1.5]:
            with self.assertRaises(ValueError):k.intake_from_bytes(b'',max_bytes=budget)
            with self.assertRaises(ValueError):k.read_bounded_source('x',max_bytes=budget)
        for value in [b'\x00',b'\xff',b'xx']:
            with self.assertRaises(k.MeasurementError):k.intake_from_bytes(value,max_bytes=1)
        self.assertEqual(k.intake_from_bytes(bytearray(b'x')).text,'x')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'hello\n');self.assertEqual(k.read_bounded_source(p).text,'hello\n')
            k.measure_file(p,language='text')
            with self.assertRaises(k.MeasurementError):k.read_bounded_source(p,max_bytes=1)
            with self.assertRaises(k.MeasurementError):k.read_bounded_source(Path(d)/'missing')
            with self.assertRaises(k.MeasurementError):k.read_bounded_source(Path(d))
            q=Path(d)/'link';q.symlink_to(p)
            with self.assertRaises(k.MeasurementError):k.read_bounded_source(q)
    def test_span_boundary(self):
        raw=k.intake_from_bytes(b'x\n')
        self.assertEqual(k._span_evidence(raw,1,1,scope='whole_artifact')['end_line'],1)
        for lo,hi in [(0,1),(2,1)]:
            with self.assertRaises(ValueError):k._span_evidence(raw,lo,hi,scope='whole_artifact')
    def test_record_corruption(self):
        rec=next(o for o in k.measure_bytes(b'x=1\n',language='python')['observations'] if o['applicability']['state']=='observed')
        for key in rec:
            x=copy.deepcopy(rec);del x[key]
            with self.assertRaises(ValueError):k.validate_observation_record(x)
        cases=[(('observation_id',),'Bad!'),(('specification_id',),'wrong'),(('record_id',),'wrong'),(('entity',),{}),(('entity','entity_id'),''),(('entity','entity_kind'),'unknown'),(('entity','path'),1),(('applicability',),{}),(('applicability','state'),'unknown'),(('applicability','reason_code'),'reason'),(('applicability','reason'),'reason'),(('value',),None),(('value',),{}),(('value',),float('inf')),(('measurement_scale',),'bad'),(('unit',),'bad'),(('source_evidence_ids',),[]),(('source_evidence_ids',),['']),(('instrumentation',),{}),(('instrumentation','component'),'bad'),(('instrumentation','algorithm_version'),'bad'),(('instrumentation','parser'),''),(('limitations',),[1])]
        for path,value in cases:
            with self.subTest(path=path,value=value),self.assertRaises(ValueError):k.validate_observation_record(setpath(copy.deepcopy(rec),path,value))
    def test_result_corruption(self):
        v=k.measure_bytes(b'def f(x):\n return x\n',language='python',path='x.py')
        cases=[(('schema',),'bad'),(('kernel_version',),'bad'),(('catalogue_schema',),'bad'),(('non_inferences',),[]),(('legacy_compatibility',),{}),(('artifact',),{}),(('artifact','language'),'bad'),(('artifact','encoding'),'bad'),(('artifact','raw_sha256'),'x'),(('artifact','normalised_sha256'),'x'),(('artifact','normalisation'),''),(('artifact','path'),1),(('source_evidence',),[]),(('source_evidence',0),{}),(('source_evidence',0,'evidence_id'),'x'),(('source_evidence',0,'normalised_sha256'),'a'*64),(('source_evidence',0,'path'),'elsewhere'),(('source_evidence',0,'start_line'),True),(('source_evidence',0,'end_line'),0),(('source_evidence',0,'scope'),'bad'),(('source_evidence',0,'end_column'),1),(('observations',),[]),(('observations',0,'entity','path'),'elsewhere'),(('observations',0,'source_evidence_ids'),['evidence:'+('a'*64)+':whole_artifact:L1-L1:C0-C0']),(('measurement_digest',),'a'*64)]
        for path,value in cases:
            with self.subTest(path=path),self.assertRaises(ValueError):k.validate_kernel_result(setpath(copy.deepcopy(v),path,value))
        for key in ['source_evidence','observations']:
            x=copy.deepcopy(v);x[key].append(copy.deepcopy(x[key][0]))
            with self.assertRaises(ValueError):k.validate_kernel_result(x)
        x=copy.deepcopy(v);x['unexpected']=0
        with self.assertRaises(ValueError):k.validate_kernel_result(x)
        x.pop('unexpected');x.pop('measurement_digest');k.validate_kernel_result(x)

class NumericContracts(unittest.TestCase):
    def test_exact_boundaries_and_bad_domain(self):
        for left,right,at,rt in [('1','0','1','0'),('0','0','0','0'),('-1','0','1','0')]:
            self.assertEqual(n.compare_decimal(left,right,absolute_tolerance=at,relative_tolerance=rt)['status'],'within_tolerance')
        for bad in [True,False,0.5,{},[],None]:
            with self.subTest(bad=bad),self.assertRaises(TypeError):n.compare_decimal(bad,'0',absolute_tolerance='0',relative_tolerance='0')
        for bad in ['NaN','sNaN','Infinity','-Infinity','not-number']:
            with self.subTest(bad=bad),self.assertRaises(ValueError):n.compare_decimal(bad,'0',absolute_tolerance='0',relative_tolerance='0')
        for at,rt in [('-1','0'),('0','-1'),('-1','-1')]:
            with self.assertRaises(ValueError):n.compare_decimal('0','0',absolute_tolerance=at,relative_tolerance=rt)
            with self.assertRaises(ValueError):n.compare_binary64(0.,0.,absolute_tolerance=at,relative_tolerance=rt)
    def test_binary_types_and_finite(self):
        for x,y in [(0,0.),(0.,0),(True,0.),(0.,True),('0',0.)]:
            with self.assertRaises(TypeError):n.compare_binary64(x,y,absolute_tolerance='0',relative_tolerance='0')
        for x,y in [(math.inf,0.),(0.,math.inf),(math.nan,0.),(0.,math.nan)]:
            with self.assertRaises(ValueError):n.compare_binary64(x,y,absolute_tolerance='0',relative_tolerance='0')
        self.assertEqual(n.compare_binary64(1.,0.,absolute_tolerance='0',relative_tolerance='0')['status'],'outside_tolerance')
        self.assertEqual(n.compare_binary64(1.,0.,absolute_tolerance='2',relative_tolerance='0')['status'],'within_tolerance')
    def test_resource_and_serialisation(self):
        from fractions import Fraction
        for bad in [0,-1,True,1.1]:
            with self.assertRaises(ValueError):n.compare_decimal('0','0',absolute_tolerance='0',relative_tolerance='0',max_work_digits=bad)
        with self.assertRaises(n.NumericResourceError):n.compare_decimal('1e100000000','0',absolute_tolerance='0',relative_tolerance='0',max_work_digits=1000)
        with self.assertRaises(n.NumericResourceError):n.compare_binary64(1.,0.,absolute_tolerance='0',relative_tolerance='0',max_work_digits=1)
        with self.assertRaises(ValueError):n._text(Fraction(1,3))
        for x in [Fraction(0),Fraction(-1,4),Fraction(1,5),Fraction(25),Fraction(1,8)]:self.assertEqual(Fraction(n._text(x)),x)
        with patch.object(n,'_rational',side_effect=MemoryError):
            with self.assertRaises(n.NumericResourceError):n.compare_decimal('1','0',absolute_tolerance='0',relative_tolerance='0')
            with self.assertRaises(n.NumericResourceError):n.compare_binary64(1.,0.,absolute_tolerance='0',relative_tolerance='0')



class InterpretationContracts(unittest.TestCase):
    def test_strict_json_and_identity(self):
        for data in ['{}',b'\xff',b'{',b'{"a":1,"a":2}',b'NaN',b'1e999',b'['*66+b'0'+b']'*66,b' '*4_000_001,b'['+b'0,'*200000+b'0]']:
            with self.subTest(data=str(data)[:80]),self.assertRaises(it.InterpretationError):it.strict_json(data)
        self.assertEqual(it.strict_json(b'{"x":[1,2]}'),{'x':[1,2]})
        for sha in ['',None,'Z'*64]:
            with self.assertRaises(it.InterpretationError):it.sha(sha)
        for x in [[],{'extra':0}]:
            with self.assertRaises(it.InterpretationError):it.fields(x,set(),'empty')
        for args in [(None,'x'),('x',None),('unknown','code')]:
            with self.assertRaises(it.InterpretationError):it.migrate_condition(*args)
        with self.assertRaises(it.InterpretationError):it._read('nonexistent.dat')
        with patch.object(it,'_read',return_value=b'changed'):
            with self.assertRaises(it.InterpretationError):it._unchanged()
    def test_profile_validation(self):
        profiles=it.available_profiles();registry=it._document('research/s04/profiles.v1.json');profile=next(p for p in registry['profiles'] if p['profile_id']=='structural-review');sha=it.digest(it.canonical(profile))
        with self.assertRaises(it.InterpretationError):it.resolve_profile('unknown',sha)
        with self.assertRaises(it.InterpretationError):it.resolve_profile('structural-review','a'*64)
        for entries in [[],[profile,profile]]:
            with patch.object(it,'_document',return_value={'profiles':entries}),self.assertRaises(it.InterpretationError):it.resolve_profile('structural-review',sha)
        changes=[(('schema',),'wrong'),(('languages',),['python']),(('task_families',),[]),(('rules',),[]),(('rules',0,'dimension_id'),'wrong'),(('rules',0,'action_id'),'unknown'),(('rules',0,'threshold_set','lower'),-1)]
        for path,value in changes:
            modified=setpath(copy.deepcopy(profile),path,value)
            with self.subTest(path=path),patch.object(it,'_document',return_value={'profiles':[modified]}),self.assertRaises(it.InterpretationError):it.resolve_profile('structural-review',sha)
    def test_threshold_regions_and_invalid_values(self):
        levels={'lower':0,'nominal':1,'upper':2}
        for value,expected in [(0,[False]),(1,[False,True]),(2,[False,True]),(3,[True])]:self.assertEqual(it.threshold_decision(value,levels)['possible_predicates'],expected)
        for val in [-1,True,1.2,'1']:
            with self.assertRaises(it.InterpretationError):it.threshold_decision(val,levels)
        for v in [True,-1,10001,1.2]:
            with self.assertRaises(it.InterpretationError):it._levels({'lower':v,'nominal':1,'upper':2})
        it._levels({'lower':0,'nominal':0,'upper':0});it._levels({'lower':10000,'nominal':10000,'upper':10000})
    def test_capsule_inputs_and_replay(self):
        p=it.available_profiles()[0];kwargs={'language':'python','profile_id':p['profile_id'],'profile_sha256':p['sha256'],'task_family':'source_inspection','path':'x.py'}
        raw=b'def f():\n return 1\n';cap=it.interpret_bytes(raw,**kwargs)
        for field,value in [('language','unknown'),('task_family','other'),('path','\x00'),('path','x'*4097),('path',1)]:
            bad={**kwargs,field:value}
            with self.assertRaises(it.InterpretationError):it.interpret_bytes(raw,**bad)
        with self.assertRaises(it.InterpretationError):it.interpret_bytes('text',**kwargs)
        with self.assertRaises(it.InterpretationError):it.verify_capsule({'x':object()},raw,**kwargs)
        with self.assertRaises(it.InterpretationError):it.verify_capsule({},raw,**kwargs)
        it.verify_capsule(cap,raw,**kwargs);self.assertTrue(it.decision_projection(cap))
    def test_vectors_including_missing_observation(self):
        p=next(p for p in it.available_profiles() if p['profile_id']=='structural-review');profile=it.resolve_profile(p['profile_id'],p['sha256'])
        for raw,lang in [(b'x=1','python'),(b'def f(:','python'),(b'# X','markdown'),(b'hello','text')]:
            cap=it.interpret_bytes(raw,language=lang,profile_id=p['profile_id'],profile_sha256=p['sha256'],task_family='source_inspection');self.assertTrue(it.decision_projection(cap))
        m=k.measure_bytes(b'def f():\n return 0\n',language='python');callables=[x for x in m['observations'] if x['entity']['entity_kind']=='python_callable'];self.assertTrue(callables)
        missing=copy.deepcopy(m);missing['observations']=[x for x in missing['observations'] if x['observation_id']!='python.callable.max_control_nesting_depth']
        vec=it._vector(missing,profile);self.assertTrue(next(x for x in vec if x['dimension_id']==it.STRUCTURE)['absences'])
        too_many=copy.deepcopy(m);too_many['observations']=callables*2000
        with self.assertRaises(it.InterpretationError):it._vector(too_many,profile)

class GateContracts(unittest.TestCase):
    def context(self):
        raw=b'def f(x):\n return x\n';p=next(p for p in it.available_profiles() if p['profile_id']=='structural-review');args={'language':'python','profile_id':p['profile_id'],'profile_sha256':p['sha256'],'task_family':'source_inspection','path':'x.py'}
        cap=it.interpret_bytes(raw,**args);record=next(x for x in cap['measurement']['observations'] if x['applicability']['state']=='observed');carrier=g.make_carrier(cap,raw,record_id=record['record_id'],**args)
        return raw,args,cap,record,carrier
    def test_context_rejection_and_missing_carriers(self):
        raw,args,cap,record,carrier=self.context();rid=record['record_id']
        for key,val in [('language','unknown'),('task_family','bad'),('path',None),('path','\x00'),('path','x'*4097)]:
            self.assertEqual(g.qualify_consumer(carrier,cap,raw,record_id=rid,**{**args,key:val})['status'],'INVALID_INPUT')
        for payload in [[],{},dict(carrier,schema='bad')]:self.assertEqual(g.qualify_consumer(payload,cap,raw,record_id=rid,**args)['status'],'INVALID_INPUT')
        self.assertEqual(g.qualify_consumer(carrier,cap,raw,record_id='another',**args)['status'],'INVALID_INPUT')
        self.assertEqual(g.qualify_consumer(None,None,raw,record_id=rid,**args)['status'],'NOT_EVALUATED')
        self.assertEqual(g.qualify_consumer(carrier,None,raw,**args)['status'],'NOT_EVALUATED')
        self.assertEqual(g.qualify_consumer(None,cap,raw,record_id=rid,**args)['status'],'NOT_EVALUATED')
        for c in [[],{},dict(cap,schema='bad')]:self.assertEqual(g.qualify_consumer(carrier,c,raw,**args)['status'],'INVALID_INPUT')
        for raw_bad in [None,'text',b'\xff']:
            self.assertEqual(g.qualify_consumer(carrier,cap,raw_bad,**args)['status'],'INVALID_INPUT')
    def test_carrier_correspondence_and_slot(self):
        raw,args,cap,record,carrier=self.context()
        changed=copy.deepcopy(carrier);changed['observation']['value']=99
        self.assertEqual(g.qualify_consumer(changed,cap,raw,**args)['admission'],'FAIL')
        duplicate=copy.deepcopy(cap);duplicate['measurement']['observations'].append(copy.deepcopy(record))
        self.assertEqual(g.qualify_consumer(carrier,duplicate,raw,**args)['status'],'INVALID_INPUT')
        changed=copy.deepcopy(cap);changed['profile']['version']='other'
        self.assertEqual(g.qualify_consumer(carrier,changed,raw,**args)['status'],'INVALID_INPUT')
        with self.assertRaises(ValueError):g._one_record(cap,'nonexistent')
        with patch.object(g,'_core_hashes',return_value={}):
            with self.assertRaises(ValueError):g._check_loaded_core()
    def test_g5_unassessed_and_invalid_profiles(self):
        pairs=('structural-review','structural-review-conservative');obs='python.callable.mccabe_complexity'
        for ids in [('structural-review',),('structural-review','structural-review'),('unknown','structural-review')]:
            with self.assertRaises(ValueError):g.compare_profiles(b'x=1',observation_id=obs,profile_ids=ids)
        for raw in [b'x=1',b'def f(:',b'def a():\n return 0\ndef b():\n return 1\n']:
            self.assertEqual(g.compare_profiles(raw,observation_id=obs,profile_ids=pairs)['status'],'NOT_EVALUATED')
        self.assertEqual(g.compare_profiles(b'def f():\n return 0\n',observation_id=obs,profile_ids=('observation-only','structural-review'))['status'],'NOT_EVALUATED')
    def test_availability_selection_and_input_domain(self):
        obs='python.callable.mccabe_complexity'
        for x in [None,{}, {'applicability':{}}, {'value':0,'applicability':{'state':'bad'}}]:self.assertEqual(g.representation_status(x),'INVALID_INPUT')
        for val in ['OTHER',None,True]:self.assertEqual(g.availability_status(val,{}),'INVALID_INPUT')
        # Invalid API parameters must be refused, not coerced to an admitted case.
        for kwargs in [dict(language='python',observation_id=3),dict(language='python',observation_id=obs,path=3)]:
            self.assertEqual(g.evaluate_availability(b'x=1',**kwargs)['status'],'INVALID_INPUT')



class BoundaryContracts(unittest.TestCase):
    def test_value_domain_bounds_and_adapter_correspondence(self):
        vals=k.measure_bytes(b'def f(x):\n if x: return 1\n return 0\n',language='python')['observations']
        for rec in vals:
            a=ad.adapt_observation(rec);r._validate_observation(a,0)
            self.assertEqual(a['value'],rec['value'])
            import hashlib
            expected=hashlib.sha256(json.dumps({key:v for key,v in a.items() if key!='fingerprint'},ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            self.assertEqual(a['fingerprint'],expected)
            if rec['applicability']['state']!='observed':self.assertEqual(a['applicability']['reason'],rec['applicability']['reason'])
            if rec['applicability']['state']=='observed':
                dom,unit,low,high,categories=k._VALUE_CONTRACTS[rec['observation_id']]
                badvals=['invalid'] if dom=='string' else ['invalid',False]
                if low is not None:badvals.append(low-1)
                if high is not None:badvals.append(high+1)
                for value in badvals:
                    x=copy.deepcopy(rec);x['value']=value
                    with self.subTest(id=rec['observation_id'],value=value),self.assertRaises(ValueError):k.validate_observation_record(x)
        x=next(copy.deepcopy(v) for v in vals if v['applicability']['state']=='observed');x['limitations']=[]
        self.assertEqual(ad.adapt_observation(x)['scope_qualification'],'Bounded by the S02 measurement specification.')
    def test_observation_constructor_contracts(self):
        x=next(o for o in k.measure_bytes(b'x=1',language='python')['observations'] if o['applicability']['state']=='observed')
        args={'entity_id':x['entity']['entity_id'],'entity_kind':x['entity']['entity_kind'],'path':'x','value':x['value'],'measurement_scale':x['measurement_scale'],'unit':x['unit'],'evidence_ids':x['source_evidence_ids'],'parser':'declared'}
        for delta in [{'state':'bad'},{'value':None},{'state':'unavailable'},{'value':{}}]:
            with self.assertRaises(ValueError):k.observation(x['observation_id'],**{**args,**delta})
        for key,val in [('entity_kind','python_callable'),('entity_id','other')]:
            y=copy.deepcopy(x);y['entity'][key]=val
            with self.assertRaises(ValueError):k.validate_observation_record(y)
        for key in k.FORBIDDEN_OUTPUT_KEYS:self.assertTrue(k._is_forbidden_identifier(key))
        with self.assertRaises(ValueError):k.measure_bytes(b'x',language='unknown')
    def test_source_feature_variants(self):
        programs=[b'import os, sys\nfrom math import sqrt\nfrom x import *\ndef f(a:int,*args:str,**kwargs:float):\n return a\n',b' \tx\n',b'\n\n',b'```bad`info\n# heading\n',b'def f():\n return 0\n']
        for raw in programs:
            for lang in ('python','markdown','text'):
                measured=k.measure_bytes(raw,language=lang);k.validate_kernel_result(measured)
        import ast
        raw=b'@decorator\ndef f():\n pass\n';intake=k.intake_from_bytes(raw);tree=ast.parse(raw);node=tree.body[0]
        self.assertEqual(k._callable_traversal_evidence(intake,node,2,3)['start_line'],1)
        for value in [None,'3',True,99]:
            changed=copy.deepcopy(node);changed.decorator_list[0].end_lineno=value
            with self.assertRaises(k.MeasurementError):k._callable_traversal_evidence(intake,changed,2,3)
    def test_catalogue_contract(self):
        catalogue=json.loads((ROOT/'research/observation-catalogue.v1.json').read_text());result=k.measure_bytes(b'def f():\n return 0\n',language='python')
        self.assertEqual(k.catalogue_observation_ids(catalogue),{r['observation_id'] for r in result['observations']})
        k.verify_result_against_catalogue(result,catalogue)
        cat=copy.deepcopy(catalogue);cat['observations']=[]
        with self.assertRaises(ValueError):k.verify_result_against_catalogue(result,cat)
        x=copy.deepcopy(result);x['observations']=[]
        with self.assertRaises(ValueError):k.verify_result_against_catalogue(x,catalogue)
        x=copy.deepcopy(result);x['observations'][0]['specification_id']='bad'
        with self.assertRaises(ValueError):k.verify_result_against_catalogue(x,catalogue)
        x=copy.deepcopy(result);next(o for o in x['observations'] if o['entity']['entity_kind']=='python_callable')['entity']['entity_kind']='source_artifact'
        with self.assertRaises(ValueError):k.verify_result_against_catalogue(x,catalogue)
        cat=copy.deepcopy(catalogue);cat['observations'][0]['instance_cardinality']='unsupported'
        with self.assertRaises(ValueError):k.verify_result_against_catalogue(result,cat)



class DiscriminatingFollowup(unittest.TestCase):
    """Added after initial sensitivity measurement; reported as adaptive.
    Tests bind documented properties, retain the original 35 and do not change
    production, inputs of the earlier campaign or its recorded score.
    """
    def test_core_symlink_and_missing_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);origin=p/'codeprobe_evidence_gates.py';origin.write_text('fixture')
            target=p/'regular';target.write_text('fixture')
            linked=p/'codeprobe_numeric_policy.py';linked.symlink_to(target)
            with patch.object(g,'__file__',str(origin)):
                with self.assertRaises(ValueError):g._core_hashes()
                linked.unlink()
                with self.assertRaises(ValueError):g._core_hashes()
                linked.write_text('fixture');self.assertEqual(set(g._core_hashes()),set(g._SOURCE_FILES))
    def test_invalid_selection_does_not_admit_source(self):
        good={'language':'python','observation_id':'python.function_def_count'}
        for key,value in [('observation_id',3),('path',3),('entity_id',3)]:
            with patch.object(k,'intake_from_bytes',wraps=k.intake_from_bytes) as admission:
                result=g.evaluate_availability(b'x=1',**{**good,key:value})
                self.assertEqual(result['G1'],'INVALID_INPUT');admission.assert_not_called()
    def test_nominal_equalities_across_declared_profiles(self):
        reg=it._document('research/s04/profiles.v1.json')
        values={rule['threshold_set']['nominal'] for p in reg['profiles'] for rule in p['rules'] if rule['observation_id']=='python.callable.mccabe_complexity'}
        for value in sorted(values):
            source=('def f(x):\n'+''.join(f' if x=={i}: x+=1\n' for i in range(value-1))+' return x\n').encode()
            result=g.compare_profiles(source,observation_id='python.callable.mccabe_complexity',profile_ids=('structural-review','structural-review-conservative'))
            self.assertEqual(result['value'],value);self.assertTrue(all(x['conformance']=='PASS' for x in result['profiles']))
    def test_binary_exact_interval_boundary(self):
        from fractions import Fraction
        from decimal import localcontext
        x,y=1.0,0.0;delta=Fraction.from_float(x);radius=(Fraction.from_float(math.ulp(x))+Fraction.from_float(math.ulp(y)))/2
        for bound,expected in [(delta+radius,'within_tolerance'),(delta-radius,'indeterminate_boundary')]:
            # Independent decimal conversion with precision sufficient for this
            # fixed dyadic denominator (2**1075); equality checked as a rational.
            with localcontext() as ctx:
                ctx.prec=2000;text=str(Decimal(bound.numerator)/Decimal(bound.denominator))
            self.assertEqual(Fraction(Decimal(text)),bound)
            self.assertEqual(n.compare_binary64(x,y,absolute_tolerance=text,relative_tolerance='0')['status'],expected)
    def test_markdown_closed_and_unclosed_fences(self):
        closed=k.measure_bytes(b'```python\n# inside\n```\n# Outside\n',language='markdown')
        opened=k.measure_bytes(b'```python\n# inside\n',language='markdown')
        c={x['observation_id']:x for x in closed['observations']};o={x['observation_id']:x for x in opened['observations']}
        self.assertEqual(c['markdown.parse_status']['value'],'complete')
        self.assertNotEqual(o['markdown.parse_status']['value'],'complete')
        self.assertEqual(c['markdown.atx_heading_count']['value'],1)

if __name__=='__main__':unittest.main()
