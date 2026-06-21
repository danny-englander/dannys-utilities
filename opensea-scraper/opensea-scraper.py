"""
OpenSea Collection Scraper
Fetches all NFT metadata, traits, and images via the OpenSea v2 API.

Usage:
    python opensea_scraper.py --api-key YOUR_API_KEY --collection COLLECTION_SLUG

Output:
    collection_data.json  — all NFT metadata and traits
    images/               — downloaded NFT images
"""

import argparse
import json
import os
import time
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse

# ── Config ──────────────────────────────────────────────────────────────────

BASE_URL        = "https://api.opensea.io/api/v2"
LIMIT           = 50          # max items per page (OpenSea cap)
RATE_LIMIT_WAIT = 0.5         # seconds between requests (free tier: ~2 req/s)
MAX_RETRIES     = 5           # retries on 429 / transient errors
IMAGE_DIR       = "images"
OUTPUT_FILE     = "collection_data.json"

# ── Helpers ──────────────────────────────────────────────────────────────────

def make_request(url: str, api_key: str, retries: int = MAX_RETRIES) -> dict:
    """GET a URL with retry/backoff on rate-limit errors."""
    req = urllib.request.Request(url, headers={
        "accept":    "application/json",
        "x-api-key": api_key,
        "User-Agent": "Mozilla/5.0",
    })
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Always read and print the error body for debugging
            try:
                err_body = e.read().decode("utf-8")
                try:
                    err_msg = json.loads(err_body)
                except Exception:
                    err_msg = err_body
            except Exception:
                err_msg = str(e)

            if e.code == 403:
                print(f"\n  ✗ 403 Forbidden — OpenSea rejected the request.")
                print(f"  URL: {url}")
                print(f"  Response: {err_msg}")
                print("\n  Common fixes:")
                print("  1. Make sure your API key is activated at https://docs.opensea.io/")
                print("  2. Double-check you copied the key correctly (no extra spaces)")
                print("  3. Some endpoints require a paid plan — try --no-collection-info to skip")
                raise SystemExit(1)
            elif e.code == 401:
                print(f"\n  ✗ 401 Unauthorized — invalid API key.")
                print(f"  Response: {err_msg}")
                raise SystemExit(1)
            elif e.code == 429:
                wait = 2 ** attempt
                print(f"  ⏳ Rate limited — waiting {wait}s (attempt {attempt}/{retries})")
                time.sleep(wait)
            elif e.code in (500, 502, 503, 504):
                wait = 2 ** attempt
                print(f"  ⚠️  Server error {e.code} — retrying in {wait}s")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  ⚠️  Error: {e} — retrying ({attempt}/{retries})")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {retries} retries: {url}")


def download_image(url: str, dest_path: str) -> bool:
    """Download an image to dest_path. Returns True on success."""
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"    ⚠️  Could not download image: {e}")
        return False


def image_ext(url: str) -> str:
    """Guess image extension from URL, default to .png."""
    if not url:
        return ".png"
    path = urlparse(url).path.lower()
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
        if path.endswith(ext):
            return ext
    return ".png"


# ── Collection info ──────────────────────────────────────────────────────────

def fetch_collection_info(api_key: str, collection_slug: str) -> dict:
    url = f"{BASE_URL}/collections/{collection_slug}"
    return make_request(url, api_key)


# ── NFT pagination ───────────────────────────────────────────────────────────

def fetch_all_nfts(api_key: str, collection_slug: str) -> list[dict]:
    """Page through all NFTs in the collection."""
    nfts   = []
    cursor = None
    page   = 1

    while True:
        url = f"{BASE_URL}/collection/{collection_slug}/nfts?limit={LIMIT}"
        if cursor:
            url += f"&next={cursor}"

        print(f"  Fetching page {page} …", end=" ", flush=True)
        data   = make_request(url, api_key)
        batch  = data.get("nfts", [])
        nfts  += batch
        cursor = data.get("next")
        print(f"{len(batch)} NFTs  (total so far: {len(nfts)})")

        if not cursor or not batch:
            break

        page += 1
        time.sleep(RATE_LIMIT_WAIT)

    return nfts


# ── Trait detail (optional enrichment) ──────────────────────────────────────

def fetch_nft_detail(api_key: str, chain: str, contract: str, token_id: str) -> dict:
    """Fetch full traits for a single NFT (sometimes richer than the list endpoint)."""
    url = f"{BASE_URL}/chain/{chain}/contract/{contract}/nfts/{token_id}"
    return make_request(url, api_key).get("nft", {})


# ── Image downloading ────────────────────────────────────────────────────────

def download_images(nfts: list[dict], image_dir: str) -> int:
    os.makedirs(image_dir, exist_ok=True)
    downloaded = 0
    total      = len(nfts)

    for i, nft in enumerate(nfts, 1):
        token_id = nft.get("identifier") or nft.get("token_id") or str(i)
        img_url  = (
            nft.get("original_image_url")   # full-res original
            or nft.get("image_url")
            or nft.get("display_image_url")
            or nft.get("display_animation_url")
        )
        ext      = image_ext(img_url)
        dest     = os.path.join(image_dir, f"{token_id}{ext}")

        if os.path.exists(dest):
            print(f"  [{i}/{total}] #{token_id} — already exists, skipping")
            continue

        print(f"  [{i}/{total}] #{token_id} — downloading …", end=" ", flush=True)
        if download_image(img_url, dest):
            print("✓")
            downloaded += 1
        else:
            print("✗ skipped")

        time.sleep(0.1)   # gentle on the CDN

    return downloaded


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OpenSea collection scraper")
    parser.add_argument("--api-key",            required=True,  help="Your OpenSea API key")
    parser.add_argument("--collection",         required=True,  help="OpenSea collection slug (e.g. midcentury-modern-design)")
    parser.add_argument("--no-images",          action="store_true", help="Skip image downloads")
    parser.add_argument("--no-collection-info", action="store_true", help="Skip collection metadata (use if getting 403 on that endpoint)")
    parser.add_argument("--output",             default=OUTPUT_FILE, help="Output JSON filename")
    args = parser.parse_args()

    print(f"\n🎨  OpenSea scraper — {args.collection}\n{'─'*50}")

    # 1. Collection-level info
    collection_info = {}
    if args.no_collection_info:
        print("\n[1/3] Skipping collection info (--no-collection-info)")
    else:
        print("\n[1/3] Fetching collection info …")
        collection_info = fetch_collection_info(args.api_key, args.collection)
        print(f"  Name  : {collection_info.get('name', '?')}")
        print(f"  Supply: {collection_info.get('total_supply', '?')}")

    # 2. All NFTs
    print("\n[2/3] Fetching NFTs …")
    nfts = fetch_all_nfts(args.api_key, args.collection)
    print(f"  ✓ {len(nfts)} NFTs fetched")

    # 3. Save JSON
    output = {
        "collection": collection_info,
        "nfts":       nfts,
        "total":      len(nfts),
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓ Data saved → {args.output}")

    # 4. Download images
    if not args.no_images:
        print(f"\n[3/3] Downloading images → ./{IMAGE_DIR}/")
        n = download_images(nfts, IMAGE_DIR)
        print(f"  ✓ {n} images downloaded")
    else:
        print("\n[3/3] Image download skipped (--no-images)")

    print(f"\n✅  Done!  JSON → {args.output}  |  Images → ./{IMAGE_DIR}/\n")


if __name__ == "__main__":
    main()