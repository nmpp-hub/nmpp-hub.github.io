import tempfile
import unittest
from pathlib import Path

from site_generation import remove_stale_auto_partials, remove_stale_pages


class GenerationCleanupTests(unittest.TestCase):
    def test_remove_stale_pages_keeps_valid_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content_dir = Path(tmpdir)
            valid_file = content_dir / "active.md"
            stale_file = content_dir / "stale.md"
            other_file = content_dir / "notes.txt"

            valid_file.write_text("active\n", encoding="utf-8")
            stale_file.write_text("stale\n", encoding="utf-8")
            other_file.write_text("notes\n", encoding="utf-8")

            removed = remove_stale_pages(content_dir, {"active"})

            self.assertEqual(removed, [stale_file])
            self.assertTrue(valid_file.exists())
            self.assertFalse(stale_file.exists())
            self.assertTrue(other_file.exists())

    def test_remove_stale_auto_partials_prunes_all_partial_types_by_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            auto_dir = Path(tmpdir)
            keep_profile = auto_dir / "active.profile.html"
            keep_publications = auto_dir / "active.publications.html"
            stale_profile = auto_dir / "stale.profile.html"
            stale_members = auto_dir / "stale.members.html"

            keep_profile.write_text("keep\n", encoding="utf-8")
            keep_publications.write_text("keep\n", encoding="utf-8")
            stale_profile.write_text("stale\n", encoding="utf-8")
            stale_members.write_text("stale\n", encoding="utf-8")

            removed = remove_stale_auto_partials(auto_dir, {"active"})

            self.assertEqual(removed, [stale_members, stale_profile])
            self.assertTrue(keep_profile.exists())
            self.assertTrue(keep_publications.exists())
            self.assertFalse(stale_profile.exists())
            self.assertFalse(stale_members.exists())


if __name__ == "__main__":
    unittest.main()
