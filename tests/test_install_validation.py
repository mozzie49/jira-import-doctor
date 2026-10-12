import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_skill', ROOT/'scripts/validate_skill.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class InstallValidationTests(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)/'jira-import-doctor'
        (root/'scripts').mkdir(parents=True)
        (root/'references').mkdir()
        (root/'SKILL.md').write_text('---\nname: jira-import-doctor\ndescription: Diagnose a CSV and log.\n---\n[Contract](references/contract.md)\n')
        (root/'scripts/jira_import_doctor.py').write_text('import csv\n')
        (root/'references/contract.md').write_text('Contract\n')
        (root/'references/sources.md').write_text('Sources\n')
        return root

    def test_valid_minimal_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(validator.validate(self.fixture(tmp))['required_frontmatter'], 'passed')

    def test_missing_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root/'SKILL.md').write_text('---\nname: jira-import-doctor\n---\n')
            with self.assertRaisesRegex(ValueError, 'description'):
                validator.validate(root)

    def test_broken_relative_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root/'references/contract.md').write_text('[Missing](no-such-file.md)')
            with self.assertRaisesRegex(ValueError, 'Broken relative link'):
                validator.validate(root)

    def test_network_import_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root/'scripts/jira_import_doctor.py').write_text('import socket\n')
            with self.assertRaisesRegex(ValueError, 'Unexpected runtime imports'):
                validator.validate(root)

    def test_dynamic_execution_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root/'scripts/jira_import_doctor.py').write_text("eval('1+1')\n")
            with self.assertRaisesRegex(ValueError, 'dynamic code'):
                validator.validate(root)


if __name__ == '__main__':
    unittest.main()
