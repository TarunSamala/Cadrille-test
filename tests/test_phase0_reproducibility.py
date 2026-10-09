"""Hard checks for the Phase 0 reproducibility freeze artifacts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


class Phase0ReproducibilityTest(unittest.TestCase):
    root = Path.cwd()

    def test_validation_base_is_digest_pinned(self) -> None:
        dockerfile = (self.root / "Dockerfile.validation").read_text(encoding="utf-8")
        first_instruction = next(
            line.strip() for line in dockerfile.splitlines() if line.strip()
        )
        self.assertRegex(first_instruction, r"^FROM .+@sha256:[0-9a-f]{64}$")

    def test_validation_requirements_are_fixed(self) -> None:
        lines = [
            line.strip()
            for line in (self.root / "requirements-validation.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertGreater(len(lines), 10)
        for line in lines:
            if " @ " in line:
                self.assertRegex(line, r"/[0-9a-f]{40}\.tar\.gz#sha256=[0-9a-f]{64}$")
            else:
                self.assertRegex(line, r"^[A-Za-z0-9_.-]+==[^=<>~]+$")
        self.assertFalse(any("/main" in line or "heads/main" in line for line in lines))
        constraints = [
            line.strip()
            for line in (self.root / "constraints-validation.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertGreater(len(constraints), 10)
        self.assertTrue(
            all(re.match(r"^[A-Za-z0-9_.-]+==[^=<>~]+$", line) for line in constraints)
        )

    def test_generated_manifests_are_present_and_scoped(self) -> None:
        output = (
            self.root
            / "docs"
            / "bible_implementation"
            / "phase_0_reproducibility"
        )
        environment = json.loads((output / "environment_manifest.json").read_text())
        licenses = json.loads((output / "dependency_license_manifest.json").read_text())
        self.assertEqual(environment["bible_phase"], "Phase 0 - Reproducibility Freeze")
        self.assertRegex(environment["source"]["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(environment["source"]["canonical_branch"], "main")
        self.assertEqual(environment["regression"]["result"], "passed")
        self.assertGreaterEqual(environment["regression"]["test_count"], 98)
        self.assertEqual(environment["gpu_validation"]["result"], "passed")
        self.assertTrue(environment["runtime"]["torch"]["cuda_available"])
        self.assertGreaterEqual(environment["gpu_validation"]["device_count"], 1)
        self.assertRegex(
            environment["research_runtime_images"]["colmap"]["image_id"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertRegex(
            environment["research_runtime_images"]["vggt"]["image_id"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertGreater(licenses["package_count"], 20)
        self.assertIn("legal review", licenses["legal_status"])

    def test_phase0_report_does_not_overclaim_completion(self) -> None:
        report = (
            self.root
            / "docs"
            / "bible_implementation"
            / "phase_0_reproducibility"
            / "PHASE0_STATUS.md"
        ).read_text()
        self.assertIn("GPU reproducibility | PASS", report)
        self.assertIn("LFS migration | DEFERRED", report)
        self.assertNotIn("manufacturing-ready", report.lower())


if __name__ == "__main__":
    unittest.main()
