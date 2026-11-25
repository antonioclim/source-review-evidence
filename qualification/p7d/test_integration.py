"""New P7D data/integration guards; existing scientific tests remain unchanged."""
from pathlib import Path
import copy
import json
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from p7d_common import Refusal, read, write, text, protected, new_output, relative
import environment
import views
ROOT=Path(__file__).resolve().parents[2]
REF=ROOT/'experiments/p7c/reference'

class IntegrationTests(unittest.TestCase):
    def test_protected_parent(self):
        x=protected(ROOT);self.assertEqual(x['source_files'],201);self.assertEqual(x['protected_files'],494)
    def test_main_timing_only(self):
        x=read(REF/'F1.json');y=copy.deepcopy(x);y[0]['start_utc']='later';y[0]['elapsed_seconds']=999
        self.assertEqual(views.main_projection(x),views.main_projection(y))
    def test_main_scientific_field_not_ignored(self):
        x=read(REF/'F1.json');y=copy.deepcopy(x);y[0]['predicate_vector']['value']='invented'
        self.assertNotEqual(views.main_projection(x),views.main_projection(y))
    def test_nested_timestamp_not_ignored(self):
        x=read(REF/'F1.json');y=copy.deepcopy(x);y[0]['details']['start_utc']='invented'
        self.assertNotEqual(views.main_projection(x),views.main_projection(y))
    def test_nontiming_root_not_ignored(self):
        x=read(REF/'oracle.json');y=copy.deepcopy(x);y['start_utc']='invented'
        self.assertNotEqual(views.main_projection(x),views.main_projection(y))
    def test_oracle_row_timing_only(self):
        x=read(REF/'oracle.json');y=copy.deepcopy(x);y['rows'][0]['elapsed_seconds']=999
        self.assertEqual(views.main_projection(x),views.main_projection(y))
    def test_oracle_measurement_change_not_ignored(self):
        x=read(REF/'oracle.json');y=copy.deepcopy(x);y['rows'][0]['measurement']['observations'][0]['value']=999
        self.assertNotEqual(views.main_projection(x),views.main_projection(y))
    def test_missing_timing_refused(self):
        x=read(REF/'F1.json');del x[0]['start_utc']
        with self.assertRaises(Refusal):views.main_projection(x)
    def test_redteam_positional_permutation(self):
        x=read(REF/'redteam.json');y=copy.deepcopy(x);rows=[r for r in y['negative_controls'] if r['id'].startswith('INVALID_VALUE')]
        for i,row in enumerate(reversed(rows)):row['id']=f'INVALID_VALUE-{i}'
        self.assertEqual(views.red_projection(x),views.red_projection(y))
    def test_redteam_reason_changed(self):
        x=read(REF/'redteam.json');y=copy.deepcopy(x);y['negative_controls'][-1]['reason']='invented'
        self.assertNotEqual(views.red_projection(x),views.red_projection(y))
    def test_redteam_duplicate_state_refused(self):
        x=read(REF/'redteam.json');x['negative_controls'][-1]['state']=x['negative_controls'][-2]['state']
        with self.assertRaises(Refusal):views.red_projection(x)
    def test_redteam_duplicate_id_refused(self):
        x=read(REF/'redteam.json');x['negative_controls'][-1]['id']=x['negative_controls'][-2]['id']
        with self.assertRaises(Refusal):views.red_projection(x)
    def test_redteam_other_case_not_ignored(self):
        x=read(REF/'redteam.json');y=copy.deepcopy(x);y['rows'][0]['status']='PASS'
        self.assertNotEqual(views.red_projection(x),views.red_projection(y))
    def test_pilot_original_negative_admitted(self):views.require_pilot(read(REF/'pilot_summary.json'))
    def test_pilot_promotion_refused(self):
        x=read(REF/'pilot_summary.json');x['P6_strict_continuation']='MET_LOCAL_SCOPE_ONLY'
        with self.assertRaises(Refusal):views.require_pilot(x)
    def test_pilot_dropped_ineligible_refused(self):
        x=read(REF/'pilot_summary.json');x['ineligible_challenges'].pop()
        with self.assertRaises(Refusal):views.require_pilot(x)
    def test_pilot_denominator_refused(self):
        x=read(REF/'pilot_summary.json');x['pairs']=29
        with self.assertRaises(Refusal):views.require_pilot(x)
    def test_pilot_a19_refused(self):
        x=read(REF/'pilot_summary.json');x['no_A19_A20_activation']=False
        with self.assertRaises(Refusal):views.require_pilot(x)
    def test_oracle_correction_does_not_mutate_raw(self):
        x={'checks':2560,'limitations':['finite',views.LEGACY_ERRATUM]};old=copy.deepcopy(x);y=views.corrected_oracle(x)
        self.assertEqual(x,old);self.assertEqual(y['checks'],2560);self.assertEqual(y['limitations'][1],views.ORACLE_CORRECTION)
    def test_oracle_unknown_text_refused(self):
        with self.assertRaises(Refusal):views.corrected_oracle({'limitations':['unknown']})
    def test_oracle_duplicate_text_refused(self):
        with self.assertRaises(Refusal):views.corrected_oracle({'limitations':[views.LEGACY_ERRATUM]*2})
    def observation(self):
        b=read(ROOT/'metadata/review-environment.observed.json')
        x={k:b[k] for k in ('python','platform','executable_sha256')};x['packages']={k:{'version':p['version'],'metadata_sha256':p['metadata_sha256'],'file_count':len(p['installed_files']),'file_mismatches':[],'files':copy.deepcopy(p['installed_files'])} for k,p in b['packages'].items()};return b,x
    def test_environment_exact_observation(self):
        b,x=self.observation();self.assertEqual(environment.evaluate(b,x),[])
    def test_environment_version_refused(self):
        b,x=self.observation();x['packages']['jsonschema']['version']='different';self.assertTrue(environment.evaluate(b,x))
    def test_environment_missing_package_refused(self):
        b,x=self.observation();del x['packages']['attrs'];self.assertTrue(environment.evaluate(b,x))
    def test_environment_changed_bytes_refused(self):
        b,x=self.observation();x['packages']['attrs']['file_mismatches']=['changed'];self.assertTrue(environment.evaluate(b,x))
    def test_environment_forged_file_list_refused(self):
        b,x=self.observation();x['packages']['attrs']['files'][0]['sha256']='0'*64
        self.assertTrue(environment.evaluate(b,x))
    def test_environment_runtime_refused(self):
        b,x=self.observation();x['python']='3.14.0';self.assertTrue(environment.evaluate(b,x))
    def test_duplicate_json_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(Refusal):read(p)
    def test_json_nan_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{"x":NaN}')
            with self.assertRaises(Refusal):read(p)
    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(Refusal):new_output(Path(d),ROOT)
    def test_output_inside_candidate_refused(self):
        with self.assertRaises(Refusal):new_output(ROOT/'must_not_create',ROOT)
    def test_path_traversal_refused(self):
        for path in ('../x','/x','a/../b','a\\b','C:x'):
            with self.assertRaises(Refusal):relative(path)
    def test_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'link';p.symlink_to(Path(d)/'absent',target_is_directory=True)
            with self.assertRaises(Refusal):new_output(p,ROOT)

if __name__=='__main__':unittest.main(verbosity=2)
