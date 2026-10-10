"""Packaging invariants necessary for installation at arbitrary paths."""
from pathlib import Path
import re
import subprocess
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/free5gc-deploy'


class Structure(unittest.TestCase):
    def test_frontmatter_and_self_contained_links(self):
        text = (SKILL / 'SKILL.md').read_text()
        self.assertTrue(text.startswith('---\n'))
        frontmatter = yaml.safe_load(text.split('---', 2)[1])
        self.assertEqual(frontmatter['name'], SKILL.name)
        self.assertIsInstance(frontmatter['description'], str)
        self.assertTrue(frontmatter['description'])
        for doc in SKILL.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
                if target.startswith(('https://', 'http://', '#')):
                    continue
                self.assertFalse(Path(target).is_absolute(), (doc, target))
                resolved = (doc.parent / target.split('#')[0]).resolve()
                self.assertTrue(resolved.is_relative_to(SKILL.resolve()), (doc, target))
                self.assertTrue(resolved.is_file(), (doc, target))

    def test_bash_syntax_all_scripts(self):
        for path in (SKILL / 'scripts').glob('*.sh'):
            with self.subTest(path=path):
                r = subprocess.run(['bash', '-n', str(path)], capture_output=True, text=True, timeout=5)
                self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__':
    unittest.main()
