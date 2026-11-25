from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISTRIBUTION = ROOT.parent


class DistributionDocumentationTests(unittest.TestCase):
    """Check the current document boundary without changing computational claims."""

    def test_current_reader_documents_exist(self):
        for relative in ("README.md", "CHANGELOG.md", "docs/EVIDENCE_AND_SCOPE.md",
                         "docs/REPRODUCIBILITY.md", "docs/DATA.md", "docs/PROVENANCE.md"):
            self.assertTrue((DISTRIBUTION / relative).is_file(), relative)

    def test_retained_technical_documentation_exists(self):
        for relative in ("docs/02-architecture.md", "docs/03-report-schema.md",
                         "docs/04-browser-security.md", "docs/05-offline-deployment.md",
                         "docs/06-calibration-guide.md", "docs/07-ui-extension-guide.md",
                         "docs/08-release-process.md", "docs/09-release-integrity.md",
                         "docs/10-provenance.md", "docs/11-design-decisions.md",
                         "docs/12-release-hash-sheet.md", "docs/13-signed-release-workflow.md",
                         "docs/14-optimisation-roadmap.md", "docs/15-final-release-audit.md",
                         "docs/16-ci-and-repository-controls.md", "docs/17-supported-coverage.md",
                         "docs/18-runtime-integrity.md", "docs/19-release-recovery.md",
                         "docs/20-worker-resilience.md", "docs/21-runtime-lifecycle.md",
                         "docs/22-contract-reconciliation.md",
                         "docs/23-measurement-scale-identity-and-numeric-policy.md",
                         "docs/assets/interface-preview.png"):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_calibration_resources_remain_available(self):
        for relative in ("calibration/01-corpus-manifest-template.csv",
                         "calibration/01-corpus-manifest-template.json",
                         "calibration/01-project-corpus-manifest-template.csv",
                         "calibration/01-project-corpus-manifest-template.json",
                         "calibration/02-calibration-profile-template.json",
                         "calibration/03-example-calibration-profile.json",
                         "calibration/04-validation-summary-template.md",
                         "calibration/profiles/README.md", "calibration/reports/.gitkeep"):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_excluded_educational_pack_and_binary_documents_are_absent(self):
        for relative in ("educator", "educator_resources", "calibration/local_profiles",
                         "calibration/validation_reports"):
            self.assertFalse((ROOT / relative).exists(), relative)
        binary_documents = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
                            if p.is_file() and p.suffix.lower() in {'.pdf', '.docx'}]
        self.assertEqual(binary_documents, [])

    def citation(self):
        # The maintained CFF representation is JSON, which is valid YAML.
        citation = json.loads((DISTRIBUTION / "CITATION.cff").read_text(encoding="utf-8"))
        self.assertIsInstance(citation, dict)
        return citation

    def test_root_citation_has_named_author_and_distribution_version(self):
        citation = self.citation()
        self.assertEqual(citation["cff-version"], "1.2.0")
        self.assertEqual(citation["authors"], [{
            "family-names": "Clim", "given-names": "Antonio",
            "orcid": "https://orcid.org/0000-0003-4745-0431",
            "affiliation": "Bucharest University of Economic Studies",
        }])
        self.assertEqual(citation["type"], "software")
        self.assertEqual(citation["version"], "1.0.0")
        self.assertEqual((DISTRIBUTION / "VERSION").read_text(encoding="utf-8").strip(), citation["version"])
        self.assertEqual(citation["title"], "Source Review Evidence: Software and Retained Computational Records")

    def test_distribution_metadata_and_component_identity_remain_distinct(self):
        document = json.loads((DISTRIBUTION / "DISTRIBUTION.json").read_text(encoding="utf-8"))
        self.assertEqual(document["version"], self.citation()["version"])
        self.assertEqual(document["technical_derivative_id"], "CP-FGCS-C2F2-FIX2")
        self.assertEqual(document["frozen_candidate_id"], "P7-R4-review-candidate+a2p7d.1")
        tree = ast.parse((ROOT / "src/codeprobe_runtime.py").read_text(encoding="utf-8"))
        version = [node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'APP_VERSION' for target in node.targets)]
        self.assertEqual(len(version), 1)
        self.assertEqual(ast.literal_eval(version[0].value), "2.3.0")

    def test_optional_public_identifiers_follow_distribution_metadata(self):
        citation = self.citation()
        document = json.loads((DISTRIBUTION / "DISTRIBUTION.json").read_text(encoding="utf-8"))
        for field, key in (("repository-code", "public_repository"), ("doi", "version_doi"),
                           ("date-released", "publication_date")):
            if document.get(key) is None:
                self.assertNotIn(field, citation)
            else:
                self.assertEqual(citation.get(field), document[key])
        self.assertFalse((ROOT / "CITATION.cff").exists())
        self.assertFalse((ROOT / "CITATION.bib").exists())

    def test_component_guide_preserves_supported_format_boundaries(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in ("Supported languages and source extensions", "Documents, databases and other file types",
                        "Input routes, folders and Git archives", "Command-line use", "Reports and exports",
                        "Input limits and exclusions"):
            self.assertIn("## " + heading, readme)
        for token in (".tsx", ".zsh", ".docx", "PDF", ".sqlite3", "No PDF/OCR"):
            self.assertIn(token, readme)


class ReferenceAndInterpretationDocumentationTests(unittest.TestCase):
    def literal(self, name):
        source = ast.parse((ROOT / "src/codeprobe_runtime.py").read_text(encoding="utf-8"))
        nodes = [n for n in source.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name]
        self.assertEqual(len(nodes), 1)
        return ast.literal_eval(nodes[0].value)

    def test_bibliographic_identity_and_revision_are_explicit(self):
        refs = self.literal("REFERENCE_LIBRARY")
        self.assertTrue(refs["chaitin"].startswith("Chaitin, G. J. (1982)."))
        self.assertIn("Register allocation & spilling via graph coloring. ACM SIGPLAN Notices.", refs["chaitin"])
        self.assertIn("10.1145/872726.806984", refs["chaitin"])
        self.assertNotIn("Auslander", refs["chaitin"])
        self.assertIn("2409.01382v1", refs["rahman_detection"])
        self.assertIn("Coghlan, A.", refs["pep8"])
        self.assertIn("0.31.2", refs["commonmark"])
        self.assertIn("Edition 5.3", refs["bash_manual"])

    def test_every_registered_reference_has_a_qualified_role(self):
        refs, roles = self.literal("REFERENCE_LIBRARY"), self.literal("REFERENCE_CONTEXT")
        self.assertEqual(set(refs), set(roles))
        for key, (role, scope) in roles.items():
            with self.subTest(key=key):
                self.assertIn(role, {"definition", "motivation", "context"})
                self.assertGreater(len(scope), 30)
        self.assertIn("not compiler liveness", roles["poletto"][1])
        self.assertIn("not the C++ Core Guidelines", roles["cpp_core"][1])

    def test_schema_and_calibration_guidance_distinguish_denominators(self):
        schema = (ROOT / "docs/03-report-schema.md").read_text(encoding="utf-8")
        guide = (ROOT / "docs/06-calibration-guide.md").read_text(encoding="utf-8")
        for field in ("evidence_coverage_basis", "aggregate_applied_weight", "effective_weight_sloc", "reference_usage", "descriptive_review_rates"):
            self.assertIn(field, schema)
        for text in (schema, guide):
            self.assertIn("not established", text)
            self.assertIn("not estimated", text)
        self.assertIn("2/4 = 0.5", guide)
        self.assertRegex(guide, r"(?s)With no eligible member of a class, `rate` is `null`.*?N/A")

    def test_uncompleted_validation_template_is_not_an_approval(self):
        text = (ROOT / "calibration/04-validation-summary-template.md").read_text(encoding="utf-8")
        for token in ("uncompleted record", "Reviewed", "Eligible", "Distinct groups", "all (pooled)", "not institutional approval", "An empty decision field is not approval"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
