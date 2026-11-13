"""Cloudflare R2 Release Publisher for Moza.

Takes the installers that tauri-action attached to the GitHub Release (downloaded into
--assets-dir), keeps one main installer per platform, and uploads them to the shared
luisenrique-releases bucket:
  moza/v<version>/  immutable, cached for a year
  moza/latest/      short cache, always the newest release
with a version.json manifest (SHA-256 per file), then enforces the retention cap (at most
3 versioned releases). The other bundle formats (.msi, .deb, .rpm, .app.tar.gz) stay on
GitHub Releases only, to keep the bucket inside the 10 GB R2 free tier.

Usage:
    set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY (and optionally R2_BUCKET_NAME)
    gh release download v0.2.0 --dir release-assets
    python scripts/publish_release_to_r2.py --version 0.2.0 --assets-dir release-assets
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prune_r2_releases import MAX_RELEASES, get_r2_client, prune_prefix_releases, validate_max_keep  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("r2.publisher")

PRODUCT = "Moza"
DEFAULT_PUBLIC_DOMAIN = "https://pub-fb9de4da4f48439ebb34b3795d05ab11.r2.dev"
# platform -> (tauri-action asset pattern, published file suffix, content type)
PLATFORMS = {
    "windows-x64": ("*_x64-setup.exe", "windows-x64-setup.exe", "application/octet-stream"),
    "macos-universal": ("*_universal.dmg", "macos-universal.dmg", "application/x-apple-diskimage"),
    "linux-x64": ("*_amd64.AppImage", "linux-x64.AppImage", "application/octet-stream"),
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_installers(assets_dir: Path) -> dict:
    """Returns {platform: path} with exactly one installer per platform, or exits."""
    found = {}
    for platform, (pattern, _, _) in PLATFORMS.items():
        matches = sorted(assets_dir.glob(pattern))
        if len(matches) != 1:
            names = sorted(p.name for p in assets_dir.iterdir()) if assets_dir.is_dir() else []
            raise SystemExit(f"Expected one {pattern} for {platform} in {assets_dir}, found {len(matches)}. Assets: {names}")
        found[platform] = matches[0]
    return found


def upload_with_retry(s3, src: Path, bucket: str, key: str, content_type: str, cache_control: str) -> None:
    for attempt in range(1, 4):
        try:
            s3.upload_file(str(src), bucket, key, ExtraArgs={"ContentType": content_type, "CacheControl": cache_control})
            logger.info("Uploaded %s -> %s (%.1f MB)", src.name, key, src.stat().st_size / 2**20)
            return
        except Exception as exc:
            if attempt == 3:
                raise
            logger.warning("Upload %d/3 of %s failed (%s); retrying in 2s...", attempt, key, exc)
            time.sleep(2)


def build_manifest(version: str, installers: dict, public: str, prefix: str) -> dict:
    platforms = {}
    for platform, path in installers.items():
        suffix = PLATFORMS[platform][1]
        name = f"{PRODUCT}-v{version}-{suffix}"
        platforms[platform] = {
            "file": name,
            "sha256": sha256_of(path),
            "size": path.stat().st_size,
            "download_url": f"{public}/{prefix}/v{version}/{name}",
            "latest_url": f"{public}/{prefix}/latest/{PRODUCT}-{suffix}",
        }
    return {
        "name": PRODUCT,
        "version": version,
        "release_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "platforms": platforms,
    }


def publish_release(version: str, assets_dir: Path, prefix: str = "moza", max_keep: int = MAX_RELEASES) -> None:
    validate_max_keep(max_keep)
    bucket = os.environ.get("R2_BUCKET_NAME", "luisenrique-releases")
    public = os.environ.get("R2_CUSTOM_DOMAIN", DEFAULT_PUBLIC_DOMAIN).rstrip("/")

    installers = find_installers(assets_dir)
    manifest = build_manifest(version, installers, public, prefix)
    manifest_file = assets_dir / "version.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    s3 = get_r2_client()
    version_dir, latest_dir = f"{prefix}/v{version}", f"{prefix}/latest"
    immutable, short = "public, max-age=31536000, immutable", "public, max-age=300"
    uploads = []
    for platform, path in installers.items():
        suffix, content_type = PLATFORMS[platform][1], PLATFORMS[platform][2]
        uploads.append((path, f"{version_dir}/{PRODUCT}-v{version}-{suffix}", content_type, immutable))
        uploads.append((path, f"{latest_dir}/{PRODUCT}-{suffix}", content_type, short))
    # Manifests last, so version.json never points at a file that is not there yet
    uploads.append((manifest_file, f"{version_dir}/version.json", "application/json", "public, max-age=86400"))
    uploads.append((manifest_file, f"{latest_dir}/version.json", "application/json", "no-cache, must-revalidate"))

    logger.info("Uploading %d objects to s3://%s/%s ...", len(uploads), bucket, prefix)
    for src, key, content_type, cache_control in uploads:
        upload_with_retry(s3, src, bucket, key, content_type, cache_control)
    for platform, entry in manifest["platforms"].items():
        logger.info("%-16s %s", platform, entry["latest_url"])
    logger.info("Update manifest: %s/%s/version.json", public, latest_dir)

    logger.info("Enforcing retention cap (max %d releases)...", max_keep)
    prune_prefix_releases(s3, bucket, prefix, max_keep=max_keep, protect_version=version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish a Moza release to Cloudflare R2")
    parser.add_argument("--version", required=True, help="Release version (e.g. 0.2.0)")
    parser.add_argument("--assets-dir", required=True, type=Path, help="Folder with the GitHub Release assets")
    parser.add_argument("--prefix", default="moza", help="Bucket folder for Moza releases")
    parser.add_argument("--max-keep", type=int, default=MAX_RELEASES, help=f"Releases to keep, 1-{MAX_RELEASES}")
    args = parser.parse_args()
    publish_release(version=args.version.lstrip("v"), assets_dir=args.assets_dir, prefix=args.prefix, max_keep=args.max_keep)
