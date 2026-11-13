"""Tests for picking the per-platform installers and building version.json (no R2 calls)."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_release_to_r2 import build_manifest, find_installers  # noqa: E402

TAURI_ASSETS = [
    "Moza_0.2.0_x64-setup.exe",
    "Moza_0.2.0_x64_en-US.msi",
    "Moza_0.2.0_universal.dmg",
    "Moza_universal.app.tar.gz",
    "Moza_0.2.0_amd64.AppImage",
    "Moza_0.2.0_amd64.deb",
    "Moza-0.2.0-1.x86_64.rpm",
]


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, names):
        for name in names:
            (self.dir / name).write_bytes(name.encode())

    def test_picks_one_main_installer_per_platform(self):
        self.make(TAURI_ASSETS)
        found = find_installers(self.dir)
        self.assertEqual({p: f.name for p, f in found.items()}, {
            "windows-x64": "Moza_0.2.0_x64-setup.exe",
            "macos-universal": "Moza_0.2.0_universal.dmg",
            "linux-x64": "Moza_0.2.0_amd64.AppImage",
        })

    def test_missing_platform_fails(self):
        self.make([a for a in TAURI_ASSETS if not a.endswith(".dmg")])
        with self.assertRaises(SystemExit) as ctx:
            find_installers(self.dir)
        self.assertIn("macos-universal", str(ctx.exception))

    def test_manifest_urls_and_checksums(self):
        self.make(TAURI_ASSETS)
        manifest = build_manifest("0.2.0", find_installers(self.dir), "https://cdn.example", "moza")
        self.assertEqual(manifest["version"], "0.2.0")
        win = manifest["platforms"]["windows-x64"]
        self.assertEqual(win["download_url"], "https://cdn.example/moza/v0.2.0/Moza-v0.2.0-windows-x64-setup.exe")
        self.assertEqual(win["latest_url"], "https://cdn.example/moza/latest/Moza-windows-x64-setup.exe")
        self.assertEqual(win["sha256"], hashlib.sha256(b"Moza_0.2.0_x64-setup.exe").hexdigest())
        self.assertEqual(set(manifest["platforms"]), {"windows-x64", "macos-universal", "linux-x64"})


if __name__ == "__main__":
    unittest.main()
