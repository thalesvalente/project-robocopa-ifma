"""Testes offline da qualidade dos artefatos Spec Kit da Feature 004."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "security_spec", ROOT / "scripts" / "verify_security_spec.py")
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)


class SecurityPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = MODULE.read_sources(ROOT)

    def replace_and_reject(self, path, search, replace):
        changed = dict(self.docs)
        changed[path] = changed[path].replace(search, replace)
        self.assertNotEqual(changed[path], self.docs[path])
        with self.assertRaises(MODULE.PlanningError):
            MODULE.validate_texts(changed)

    def test_valid(self):
        result = MODULE.validate(ROOT)
        self.assertEqual(result["functional_requirements"], 20)
        self.assertEqual(result["success_criteria"], 8)
        self.assertEqual(result["threats"], 16)
        self.assertEqual(result["tasks_pending"], 39)
        self.assertEqual(result["security_gates_unapproved"], 18)

    def test_missing_fr(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/spec.md",
                                "- **FR-008**:", "- **FR-008-REMOVED**:")

    def test_missing_sc(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/spec.md",
                                "- **SC-003**:", "- **SC-003-REMOVED**:")

    def test_missing_threat(self):
        self.replace_and_reject(MODULE.THREATS, "| TH-16 |", "| TH-XX |")

    def test_missing_question(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/clarifications.md",
                                "| Q-05 |", "| Q-XX |")

    def test_missing_task(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/tasks.md",
                                "- [ ] T039 [US5]", "- [ ] TXX9 [US5]")

    def test_invalid_requirement_ref(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/tasks.md",
                                "FR-007; SC-002", "FR-099; SC-002")

    def test_requirements_not_hidden_by_crosscutting_task(self):
        path = f"{MODULE.FEATURE}/tasks.md"
        changed = dict(self.docs)
        changed[path] = changed[path].replace("FR-008, FR-017;", "FR-008;")
        changed[path] = changed[path].replace("FR-013, FR-017;", "FR-013;")
        with self.assertRaises(MODULE.PlanningError):
            MODULE.validate_texts(changed)

    def test_mark_implementation_done_rejected(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/tasks.md",
                                "- [ ] T001", "- [x] T001")

    def test_approve_gate_without_evidence_rejected(self):
        self.replace_and_reject(f"{MODULE.FEATURE}/checklists/security-gates.md",
                                "- [ ] SG001", "- [x] SG001")

    def test_scope_explicitly_documental(self):
        self.assertIn("NAO E TESTE DE SANDBOX", MODULE.validate(ROOT)["scope"])


if __name__ == "__main__":
    unittest.main()
