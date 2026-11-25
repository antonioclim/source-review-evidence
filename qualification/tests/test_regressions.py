"""P7A tests frozen before production edits; source root supplied by the runner."""
import copy
import decimal
from decimal import Decimal, localcontext
from fractions import Fraction
import importlib
import math
import unittest
from unittest.mock import patch

import codeprobe_numeric_policy as num
import codeprobe_interpretation as ip
import codeprobe_measurement_kernel as mk
import codeprobe_s01_observation_adapter as ad

try:
    import codeprobe_evidence_gates as gates
except ModuleNotFoundError:
    gates = None

DEC='1.0000000000000000000000000001'
BTOL='0.100000000000000012490009027'

class NumericRegression(unittest.TestCase):
    def test_P3_decimal_false_admission(self):
        self.assertEqual(num.compare_decimal(DEC,'0',absolute_tolerance='1',relative_tolerance='0')['status'],'outside_tolerance')
    def test_P3_binary_strict_interior(self):
        witness=Fraction(Decimal('0.1000000000000000124900090270165055398829281330108642578125'))
        centre=Fraction.from_float(0.1); radius=Fraction.from_float(math.ulp(0.1))/2
        self.assertTrue(centre-radius<witness<centre+radius)
        self.assertGreater(witness,Fraction(Decimal(BTOL)))
        self.assertEqual(num.compare_binary64(0.1,0.0,absolute_tolerance=BTOL,relative_tolerance='0')['status'],'indeterminate_boundary')
    def test_exact_serialisation(self):
        r=num.compare_decimal(DEC,'0',absolute_tolerance='1',relative_tolerance='0')
        self.assertEqual(Fraction(Decimal(r['left'])),Fraction(Decimal(DEC)))
        self.assertEqual(Fraction(Decimal(r['delta'])),Fraction(Decimal(DEC)))
    def test_context_invariance(self):
        results=[]
        for prec in (2,28,29,50,80):
            with localcontext() as c:
                c.prec=prec; c.rounding=decimal.ROUND_FLOOR
                results.append(num.compare_decimal(DEC,'0',absolute_tolerance='1',relative_tolerance='0'))
        self.assertTrue(all(x==results[0] for x in results)); self.assertEqual(results[0]['status'],'outside_tolerance')
    def test_active_traps_and_context_not_mutated(self):
        with localcontext() as c:
            c.prec=2; c.traps[decimal.Inexact]=True; c.traps[decimal.Rounded]=True
            c.clear_flags(); old=dict(c.flags)
            self.assertEqual(num.compare_decimal(DEC,'0',absolute_tolerance='1',relative_tolerance='0')['status'],'outside_tolerance')
            self.assertEqual(dict(c.flags),old)
    def test_M028_inclusive_equality(self):
        self.assertEqual(num.compare_decimal('2','1',absolute_tolerance='1',relative_tolerance='0')['status'],'within_tolerance')
    def test_M026_single_negative_tolerance(self):
        for at,rt in (('-1','0'),('0','-1')):
            with self.assertRaises(ValueError): num.compare_decimal('0','0',absolute_tolerance=at,relative_tolerance=rt)
    def test_M025_float_refusal(self):
        with self.assertRaises(TypeError): num.compare_decimal(0.1,'0',absolute_tolerance='1',relative_tolerance='0')
    def test_unsupported_type_refused(self):
        class Disguised:
            def __str__(self): return '1'
        with self.assertRaises(TypeError): num.compare_decimal(Disguised(),'1',absolute_tolerance='0',relative_tolerance='0')
    def test_long_lexical_no_implicit_digit_cap(self):
        s='1234567890'*450
        r=num.compare_decimal(s,s,absolute_tolerance='0',relative_tolerance='0')
        self.assertEqual(r['status'],'within_tolerance')
        self.assertEqual(Decimal(r['left']),Decimal(s))
    def test_resource_budget_is_explicit(self):
        self.assertTrue(hasattr(num,'NumericResourceError'),'new resource-error API absent')
        with self.assertRaises(num.NumericResourceError) as e:
            num.compare_decimal('1e100000000','0',absolute_tolerance='1',relative_tolerance='0',max_work_digits=1000)
        self.assertEqual(e.exception.status,'RESOURCE_REFUSED')
    def test_allocation_failure_is_resource_refusal(self):
        self.assertTrue(hasattr(num,'NumericResourceError'),'new resource-error API absent')
        with patch.object(num,'_pow10',side_effect=MemoryError('injected allocation refusal')):
            with self.assertRaises(num.NumericResourceError):
                num.compare_decimal('1e50','0',absolute_tolerance='0',relative_tolerance='0')
    def test_binary_invalid(self):
        for v in (float('inf'),float('-inf'),float('nan')):
            with self.assertRaises(ValueError): num.compare_binary64(v,0.0,absolute_tolerance='0',relative_tolerance='0')
        with self.assertRaises(TypeError): num.compare_binary64(1,0.0,absolute_tolerance='0',relative_tolerance='0')
    def test_decimal_invalid(self):
        for v in ('NaN','sNaN','Inf','broken'):
            with self.assertRaises(ValueError): num.compare_decimal(v,'0',absolute_tolerance='0',relative_tolerance='0')
        with self.assertRaises(TypeError): num.compare_decimal(True,'0',absolute_tolerance='0',relative_tolerance='0')
    def test_huge_integer_no_runtime_string_cap(self):
        n=10**4500+123
        r=num.compare_decimal(n,n,absolute_tolerance=0,relative_tolerance=0)
        self.assertEqual(r['status'],'within_tolerance'); self.assertEqual(Decimal(r['left']),Decimal(n))

class GateIntegration(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(gates,'new P6 gate API is absent from the historical candidate')
        self.src=b'def f(x):\n    if x:\n        return 1\n    return 0\n'
        self.kw=dict(language='python',profile_id='structural-review',profile_sha256={p['profile_id']:p['sha256'] for p in ip.available_profiles()}['structural-review'],task_family='source_inspection',path='p7a.py')
        self.cap=ip.interpret_bytes(self.src,**self.kw)
        self.r=next(r for r in self.cap['measurement']['observations'] if r['observation_id']=='python.callable.mccabe_complexity')
        self.car=gates.make_carrier(self.cap,self.src,record_id=self.r['record_id'],**self.kw)
    def test_zero_observed_passes_G2(self):
        r=gates.evaluate_availability(b'pass\n',language='python',observation_id='python.function_definition_count')
        self.assertEqual(r['status'],'PASS'); self.assertEqual(r['record']['value'],0)
    def test_syntax_unavailable_is_valid_G2_fail(self):
        r=gates.evaluate_availability(b'def f(:\n',language='python',observation_id='python.function_definition_count')
        self.assertEqual(r['G1'],'PASS'); self.assertEqual(r['V2'],'PASS'); self.assertEqual(r['status'],'FAIL'); self.assertEqual(r['record']['applicability']['state'],'unavailable')
    def test_bad_bytes_not_evaluated(self):
        r=gates.evaluate_availability(b'\xff',language='python',observation_id='python.function_definition_count')
        self.assertEqual((r['G1'],r['status']),('FAIL','NOT_EVALUATED'))
    def test_ambiguous_slot_refused(self):
        r=gates.evaluate_availability(b'def f():\n    pass\ndef g():\n    pass\n',language='python',observation_id='python.callable.mccabe_complexity')
        self.assertEqual(r['status'],'INVALID_INPUT')
    def test_G6_bound_admission_and_replay(self):
        r=gates.qualify_consumer(self.car,self.cap,self.src,**self.kw)
        self.assertEqual((r['status'],r['admission'],r['replay']),('PASS','PASS','PASS'))
    def test_G6_raw_ID_not_admitted(self):
        c=copy.deepcopy(self.car); c['observation']['source_evidence'][0]['evidence_id']=self.r['source_evidence_ids'][0]
        r=gates.qualify_consumer(c,self.cap,self.src,**self.kw)
        self.assertEqual((r['status'],r['admission'],r['replay']),('FAIL','FAIL','PASS'))
    def test_G6_rehashed_capsule_fails_replay(self):
        cap=copy.deepcopy(self.cap); x=next(r for r in cap['measurement']['observations'] if r['observation_id']=='source.byte_count'); x['value']+=1
        cap['measurement']['measurement_digest']=mk.sha256_hex(mk.canonical_json(mk._measurement_digest_scope(cap['measurement'])).encode())
        mk.validate_kernel_result(cap['measurement']); cap.pop('digest'); cap['digest']=ip.digest(ip.canonical(cap))
        r=gates.qualify_consumer(self.car,cap,self.src,**self.kw)
        self.assertEqual((r['status'],r['admission'],r['replay']),('FAIL','PASS','FAIL'))
    def test_G6_other_source_invalid_binding(self):
        r=gates.qualify_consumer(self.car,self.cap,self.src+b'\n',**self.kw)
        self.assertEqual(r['status'],'INVALID_INPUT')
    def test_G6_other_profile_invalid_binding(self):
        kw=dict(self.kw); kw['profile_id']='structural-review-conservative'; kw['profile_sha256']={p['profile_id']:p['sha256'] for p in ip.available_profiles()}[kw['profile_id']]
        self.assertEqual(gates.qualify_consumer(self.car,self.cap,self.src,**kw)['status'],'INVALID_INPUT')
    def test_G6_forged_context_invalid(self):
        c=copy.deepcopy(self.car); c['context']['raw_sha256']='0'*64
        self.assertEqual(gates.qualify_consumer(c,self.cap,self.src,**self.kw)['status'],'INVALID_INPUT')
    def test_G6_forged_build_invalid(self):
        cap=copy.deepcopy(self.cap); cap['build']['implementation_digest']='0'*64
        self.assertEqual(gates.qualify_consumer(self.car,cap,self.src,**self.kw)['status'],'INVALID_INPUT')
    def test_G6_missing_subcheck_not_pass(self):
        a=gates.qualify_consumer(None,self.cap,self.src,record_id=self.r['record_id'],**self.kw)
        b=gates.qualify_consumer(self.car,None,self.src,**self.kw)
        self.assertEqual((a['status'],a['admission'],a['replay']),('NOT_EVALUATED','NOT_EVALUATED','PASS'))
        self.assertEqual((b['status'],b['admission'],b['replay']),('NOT_EVALUATED','PASS','NOT_EVALUATED'))
    def test_G6_valid_but_different_value_refused(self):
        c=copy.deepcopy(self.car); c['observation']['value']+=1
        c['observation']['fingerprint']=ip.digest(ip.canonical({k:v for k,v in c['observation'].items() if k!='fingerprint'}))
        self.assertEqual(gates.qualify_consumer(c,self.cap,self.src,**self.kw)['status'],'FAIL')
    def test_G5_profile_relation_both_conformant(self):
        src=('def f(x):\n'+''.join(f'    if x == {i}:\n        x += 1\n' for i in range(12))+'    return x\n').encode()
        r=gates.compare_profiles(src,observation_id='python.callable.mccabe_complexity',profile_ids=('structural-review','structural-review-conservative'),path='p7a.py')
        self.assertEqual(r['status'],'RELATIONAL_WITNESS'); self.assertEqual(r['value'],13)
        self.assertEqual([x['conformance'] for x in r['profiles']],['PASS','PASS'])
        self.assertNotEqual(r['profiles'][0]['decision'],r['profiles'][1]['decision'])
    def test_G5_equivalent_is_preserved(self):
        r=gates.compare_profiles(b'def f():\n    pass\n',observation_id='python.callable.mccabe_complexity',profile_ids=('structural-review','structural-review-conservative'))
        self.assertEqual(r['status'],'NO_DIFFERENCE'); self.assertEqual([p['conformance'] for p in r['profiles']],['PASS','PASS'])
