import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PhaseNamingTests(unittest.TestCase):
    def test_phase_authority_and_directory_contract(self):
        registry_path = ROOT / "docs" / "phase_registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        self.assertEqual(registry["canonical_system"], "bible_v1_0")
        bible = registry["systems"]["bible_v1_0"]
        legacy = registry["systems"]["legacy_pipeline"]
        self.assertTrue(bible["canonical"])
        self.assertFalse(legacy["canonical"])
        self.assertEqual([item["id"] for item in bible["phases"]], [str(i) for i in range(10)])
        self.assertIn("3.3.2", [item["id"] for item in legacy["phases"]])

        for relative in (
            "docs/bible_v1_0",
            "docs/bible_implementation",
            "docs/legacy_pipeline",
            "docs/research",
            "pipeline/README.md",
            "tests/README.md",
        ):
            self.assertTrue((ROOT / relative).exists(), relative)

        self.assertFalse((ROOT / "docs/lalitha_project_bible_v1_0").exists())
        self.assertFalse((ROOT / "docs/reproducibility").exists())

        for relative in ("README.md", "data/README.md", "dataset/README.md", "pipeline/README.md"):
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertIn("legacy", text, relative)


if __name__ == "__main__":
    unittest.main()
