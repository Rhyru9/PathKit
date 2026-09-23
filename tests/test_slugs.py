"""
tests/test_slugs.py — Integration tests for models.slugs and all detectors.
"""

import json
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.slugs import URLIntentModel, extract, run
from models.decision import classify_path
from models.encoding import decode
from eval.baselines import auto_label_pool
from scripts.retrain_eval import auto_label_paths


class TestSlugPipeline(unittest.TestCase):
    """End-to-end pipeline test."""

    @classmethod
    def setUpClass(cls):
        cls.weights_path = "weights/slugs_v4.json"
        cls.output_dir = "output/slugs"

    def test_1_classify_runs(self):
        """Full pipeline completes without error."""
        t0 = time.time()
        model = run(
            paths_txt="data/paths.txt",
            output_dir=self.output_dir,
            weights_file=self.weights_path,
        )
        elapsed = time.time() - t0
        self.assertIsNotNone(model)
        self.assertLess(elapsed, 120, "Pipeline took too long")

    def test_2_predict_single(self):
        """Single prediction returns expected structure."""
        model = URLIntentModel()
        result = model.predict("panduan-belajar-online")
        self.assertIn("final", result)
        self.assertIn("confidence", result)
        self.assertIn("scores", result)
        self.assertIn("is_uncertain", result)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_3_save_load_roundtrip(self):
        """Model save/load preserves predictions."""
        model = URLIntentModel()
        model.train("panduan-belajar-online", "slug", weight=2.0)
        model.train("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6", "random_id", weight=2.0)

        before = model.predict("panduan-belajar-online")["final"]
        model.save(self.weights_path)

        model2 = URLIntentModel()
        model2.load(self.weights_path)
        after = model2.predict("panduan-belajar-online")["final"]

        self.assertEqual(before, after, "Save/load roundtrip failed")

    def test_4_feature_extraction(self):
        """Feature vector has expected dimensions."""
        feats = extract("panduan-belajar-online")
        self.assertEqual(len(feats), 24, f"Expected 24 features, got {len(feats)}")
        self.assertGreater(feats["readable_count_norm"], 0)
        self.assertEqual(feats["has_dash"], 1.0)

    def test_5_output_files_exist(self):
        """Pipeline output files are created and non-empty."""
        expected = [
            "slugs.txt",
            "slugs_review.txt",
            "slugs_with_conf.json",
            "summary.json",
        ]
        for fname in expected:
            path = os.path.join(self.output_dir, fname)
            self.assertTrue(os.path.isfile(path), f"Missing: {path}")
            self.assertGreater(os.path.getsize(path), 0, f"Empty: {path}")

    def test_6_summary_json_valid(self):
        """Summary JSON is valid and has expected keys."""
        with open(os.path.join(self.output_dir, "summary.json")) as f:
            s = json.load(f)
        self.assertIn("total_paths", s)
        self.assertIn("distribution", s)
        self.assertIn("slugs_exported", s)

    def test_7_slug_meta_valid(self):
        """Slug metadata JSON is valid."""
        with open(os.path.join(self.output_dir, "slugs_with_conf.json")) as f:
            meta = json.load(f)
        self.assertGreater(len(meta), 0)
        first = next(iter(meta.values()))
        self.assertIn("confidence", first)
        self.assertIn("decoded", first)


class TestDetectors(unittest.TestCase):
    """All 5 detectors return expected scores."""

    def test_uuid_detects_standalone(self):
        from models.uuid import score

        self.assertEqual(score("550e8400-e29b-41d4-a716-446655440000"), 1.0)

    def test_uuid_rejects_slug(self):
        from models.uuid import score

        self.assertEqual(score("panduan-belajar-online"), 0.0)

    def test_timestamp_detects_unix(self):
        from models.timestamp import score

        self.assertGreater(score("/log/1718201234"), 0.5)

    def test_timestamp_rejects_slug(self):
        from models.timestamp import score

        self.assertEqual(score("panduan-belajar-online"), 0.0)

    def test_hash_detects_md5(self):
        from models.hash import score

        self.assertGreater(score("9e107d9d372bb6826bd81d3542a419d6"), 0.5)

    def test_hash_rejects_slug(self):
        from models.hash import score

        self.assertEqual(score("panduan-belajar-online"), 0.0)

    def test_hash_skips_uuid(self):
        from models.hash import score

        self.assertEqual(score("550e8400-e29b-41d4-a716-446655440000"), 0.0)

    def test_base64_detects_jwt(self):
        from models.base64 import score

        self.assertGreater(
            score("eyJpdiI6Ii9CVlVOWkcyeWFxVWY2d3BqSVh6dHc9PSIsInZhbHVlIjoiVkZF"), 0.5
        )

    def test_base64_rejects_slug(self):
        from models.base64 import score

        self.assertEqual(score("panduan-belajar-online"), 0.0)

    def test_other_detects_org_unit(self):
        from models.other import score

        self.assertGreater(score("ditjen=5Fbudaya=5Fsesditjen=5Fupt26"), 0.5)

    def test_other_rejects_slug(self):
        from models.other import score

        self.assertEqual(score("panduan-belajar-online"), 0.0)

    def test_decode_preserves_query_values(self):
        self.assertEqual(decode("/search?page=20"), "/search?page=20")
        self.assertEqual(
            decode("tabs.php%3Fnpsn%3D10800463"),
            "tabs.php?npsn=10800463",
        )

    def test_decode_supports_utf8(self):
        self.assertEqual(decode("caf%C3%A9"), "café")

    def test_decode_handles_routing_hex_in_path(self):
        self.assertEqual(decode("setjen%3D5Fpdspk"), "setjen_pdspk")

    def test_canonical_flow_uses_consistent_labels(self):
        model = URLIntentModel()
        self.assertEqual(classify_path("/search?page=20", model).label, "search")
        self.assertEqual(
            classify_path("setjen%3D5Fpdspk", model).label, "encoded"
        )

    def test_baseline_uses_canonical_training_labels(self):
        paths = ["caf%C3%A9", "setjen%3D5Fpdspk", "report.pdf", "12345678-1234"]
        self.assertEqual(auto_label_pool(paths), auto_label_paths(paths))

    def test_ablation_rejects_unknown_stage(self):
        with self.assertRaises(ValueError):
            classify_path(
                "panduan-belajar-online",
                URLIntentModel(),
                disabled=frozenset({"typo"}),
            )

    def test_ablation_can_disable_ml_with_fallback(self):
        result = classify_path(
            "panduan-belajar-online",
            URLIntentModel(),
            fallback_label="slug",
            disabled=frozenset({"ml"}),
        )
        self.assertEqual(result.label, "slug")


if __name__ == "__main__":
    unittest.main()
