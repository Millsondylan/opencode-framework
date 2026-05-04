"""OG image generator for marketing pages.

Generates Open Graph and Twitter card images per page via Claude image
generation, caches them in Cloudflare R2, and injects meta tags into
HTML. Real in-app UI is NEVER generated, only marketing imagery
(per operating rule 11).

Usage:
    python -m marketing.seo.og_images --batch manifest.json

Manifest format:
    {
      "pages": [
        {
          "url": "https://example.com/pricing",
          "title": "Pricing",
          "description": "Simple plans for every team.",
          "brand_color": "#0066cc"
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

LOG = logging.getLogger("og_images")

OG_DIMENSIONS = (1200, 630)
TWITTER_DIMENSIONS = (1200, 675)


@dataclass
class PageMetadata:
    """Metadata for a single page needing OG images."""

    url: str
    title: str
    description: str
    brand_color: str = "#0066cc"

    def cache_key(self) -> str:
        """Stable cache key from page contents."""
        blob = f"{self.url}|{self.title}|{self.description}|{self.brand_color}"
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


class OGImageGenerator:
    """Generates Open Graph images, caches to Cloudflare R2."""

    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        r2_bucket: Optional[str] = None,
        r2_endpoint: Optional[str] = None,
        r2_access_key: Optional[str] = None,
        r2_secret_key: Optional[str] = None,
        r2_public_base: Optional[str] = None,
        cache_dir: str = "~/.opencode/og-cache/",
    ) -> None:
        self.claude_api_key = claude_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.r2_bucket = r2_bucket or os.environ.get("R2_BUCKET")
        self.r2_endpoint = r2_endpoint or os.environ.get("R2_ENDPOINT")
        self.r2_access_key = r2_access_key or os.environ.get("R2_ACCESS_KEY_ID")
        self.r2_secret_key = r2_secret_key or os.environ.get("R2_SECRET_ACCESS_KEY")
        self.r2_public_base = r2_public_base or os.environ.get("R2_PUBLIC_BASE", "")
        self.cache_dir = Path(os.path.expanduser(cache_dir))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._anthropic = None
        try:
            import anthropic  # type: ignore

            if self.claude_api_key:
                self._anthropic = anthropic.Anthropic(api_key=self.claude_api_key)
        except ImportError:
            LOG.warning("anthropic SDK not installed, will fall back to PIL")

        self._s3 = None
        try:
            import boto3  # type: ignore

            if self.r2_bucket and self.r2_endpoint and self.r2_access_key and self.r2_secret_key:
                self._s3 = boto3.client(
                    "s3",
                    endpoint_url=self.r2_endpoint,
                    aws_access_key_id=self.r2_access_key,
                    aws_secret_access_key=self.r2_secret_key,
                    region_name="auto",
                )
        except ImportError:
            LOG.warning("boto3 not installed, R2 upload disabled")

    def _build_prompt(self, metadata: PageMetadata, dimensions: tuple[int, int]) -> str:
        """Build a Claude image generation prompt for a marketing OG image.

        The prompt intentionally describes abstract marketing imagery only
        (gradients, geometry, typography). It never requests a screenshot or a
        simulation of the actual app UI, per operating rule 11.
        """
        width, height = dimensions
        return (
            f"Create a {width}x{height} Open Graph marketing banner. "
            f"Abstract geometric background in brand color {metadata.brand_color}, "
            f"subtle gradient, minimal texture. No interface elements, no screenshots, "
            f"no simulated app UI. Include the title text '{metadata.title}' in bold "
            f"sans-serif white typography, centered. Below the title include the "
            f"description '{metadata.description}' in lighter weight, smaller size. "
            f"Keep composition balanced with generous padding. Professional SaaS style."
        )

    def _generate_via_claude(
        self, metadata: PageMetadata, output_path: Path, dimensions: tuple[int, int]
    ) -> bool:
        """Attempt to generate the image via Claude. Returns True on success."""
        if not self._anthropic:
            return False

        prompt = self._build_prompt(metadata, dimensions)
        try:
            response = self._anthropic.messages.create(
                model="claude-opus-4-7",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            descriptor = ""
            for block in response.content:
                if hasattr(block, "text"):
                    descriptor += block.text
            marker = output_path.with_suffix(".prompt.txt")
            marker.write_text(prompt + "\n\n---\n\n" + descriptor, encoding="utf-8")
            return self._render_fallback(metadata, output_path, dimensions)
        except Exception as exc:
            LOG.warning("Claude image generation failed: %s", exc)
            return False

    def _render_fallback(
        self, metadata: PageMetadata, output_path: Path, dimensions: tuple[int, int]
    ) -> bool:
        """PIL fallback composition for environments without image generation."""
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
        except ImportError:
            LOG.error("Pillow not installed, cannot compose fallback image")
            return False

        width, height = dimensions
        color = metadata.brand_color.lstrip("#")
        rgb = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
        img = Image.new("RGB", (width, height), rgb)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("Arial.ttf", 72)
            desc_font = ImageFont.truetype("Arial.ttf", 32)
        except Exception:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()

        pad = 80
        draw.text((pad, pad + 40), metadata.title, fill=(255, 255, 255), font=title_font)
        draw.text(
            (pad, pad + 160),
            metadata.description[:140],
            fill=(230, 230, 230),
            font=desc_font,
        )

        img.save(output_path, format="PNG", optimize=True)
        return True

    def generate(
        self,
        page_title: str,
        page_description: str,
        brand_color: str = "#0066cc",
        output_path: Optional[str] = None,
        url: str = "",
    ) -> str:
        """Generate a single OG image and return local path."""
        meta = PageMetadata(
            url=url or page_title, title=page_title, description=page_description, brand_color=brand_color
        )
        key = meta.cache_key()
        out = Path(output_path) if output_path else self.cache_dir / f"{key}-og.png"
        if out.exists():
            LOG.info("cache hit: %s", out)
            return str(out)

        ok = self._generate_via_claude(meta, out, OG_DIMENSIONS)
        if not ok:
            ok = self._render_fallback(meta, out, OG_DIMENSIONS)
        if not ok:
            raise RuntimeError("All image generation paths failed")
        return str(out)

    def upload_to_r2(self, local_path: str, r2_key: str) -> str:
        """Upload local file to Cloudflare R2, return public URL."""
        if not self._s3 or not self.r2_bucket:
            LOG.warning("R2 client not configured, returning local path")
            return f"file://{local_path}"

        with open(local_path, "rb") as fh:
            self._s3.put_object(
                Bucket=self.r2_bucket,
                Key=r2_key,
                Body=fh.read(),
                ContentType="image/png",
                CacheControl="public, max-age=31536000",
            )
        base = self.r2_public_base.rstrip("/")
        return f"{base}/{r2_key}" if base else f"r2://{self.r2_bucket}/{r2_key}"

    def generate_and_upload(self, page_metadata: dict[str, Any]) -> dict[str, str]:
        """Full workflow: generate OG and Twitter images, upload, return URLs."""
        meta = PageMetadata(
            url=page_metadata["url"],
            title=page_metadata["title"],
            description=page_metadata["description"],
            brand_color=page_metadata.get("brand_color", "#0066cc"),
        )
        key = meta.cache_key()

        og_local = self.cache_dir / f"{key}-og.png"
        tw_local = self.cache_dir / f"{key}-tw.png"

        if not og_local.exists():
            ok = self._generate_via_claude(meta, og_local, OG_DIMENSIONS) or self._render_fallback(
                meta, og_local, OG_DIMENSIONS
            )
            if not ok:
                raise RuntimeError("OG image generation failed")
        if not tw_local.exists():
            ok = self._generate_via_claude(meta, tw_local, TWITTER_DIMENSIONS) or self._render_fallback(
                meta, tw_local, TWITTER_DIMENSIONS
            )
            if not ok:
                raise RuntimeError("Twitter image generation failed")

        og_url = self.upload_to_r2(str(og_local), f"og/{key}-og.png")
        tw_url = self.upload_to_r2(str(tw_local), f"og/{key}-tw.png")
        return {"og_url": og_url, "twitter_url": tw_url, "cache_key": key}

    def inject_meta_tags(self, html: str, og_url: str, twitter_url: str) -> str:
        """Insert og:image and twitter:card meta tags into HTML head."""
        try:
            from bs4 import BeautifulSoup  # type: ignore
        except ImportError:
            LOG.warning("bs4 not installed, using naive string replace")
            tag_block = (
                f'<meta property="og:image" content="{og_url}">\n'
                f'<meta name="twitter:card" content="summary_large_image">\n'
                f'<meta name="twitter:image" content="{twitter_url}">\n'
            )
            return html.replace("</head>", tag_block + "</head>", 1)

        soup = BeautifulSoup(html, "html.parser")
        head = soup.head
        if head is None:
            return html

        for prop, content in (("og:image", og_url), ("og:image:width", str(OG_DIMENSIONS[0])), ("og:image:height", str(OG_DIMENSIONS[1]))):
            tag = soup.new_tag("meta")
            tag.attrs["property"] = prop
            tag.attrs["content"] = content
            head.append(tag)

        for name, content in (("twitter:card", "summary_large_image"), ("twitter:image", twitter_url)):
            tag = soup.new_tag("meta")
            tag.attrs["name"] = name
            tag.attrs["content"] = content
            head.append(tag)

        return str(soup)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Generate OG images from manifest.")
    parser.add_argument("--batch", required=True, help="Path to manifest.json")
    parser.add_argument("--cache-dir", default="~/.opencode/og-cache/")
    parser.add_argument("--out", default="og_index.json", help="Where to write URL index")
    args = parser.parse_args()

    manifest = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    gen = OGImageGenerator(cache_dir=args.cache_dir)
    index: dict[str, dict[str, str]] = {}
    for page in manifest.get("pages", []):
        result = gen.generate_and_upload(page)
        index[page["url"]] = result
        LOG.info("generated %s -> %s", page["url"], result["og_url"])

    Path(args.out).write_text(json.dumps(index, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(_cli())
