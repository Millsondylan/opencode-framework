"""Sitemap and robots.txt generator for marketing sites.

Auto-generates sitemap.xml (and sitemap index when over 50000 URLs) plus
robots.txt at build time. Supports hreflang alternates for 10 locales:
en, es, pt-BR, de, fr, ja, ko, hi, id, ar.

Usage:
    python -m marketing.seo.sitemap --manifest manifest.json --out dist/

Manifest format:
    {
      "site_url": "https://example.com",
      "urls": [
        {
          "path": "/pricing",
          "lastmod": "2026-04-24",
          "changefreq": "weekly",
          "priority": 0.9,
          "hreflang": {"en": "/pricing", "es": "/es/precios"}
        }
      ],
      "robots": {
        "allow": ["/"],
        "disallow": ["/admin/", "/internal/"]
      }
    }
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape

LOG = logging.getLogger("sitemap")

SUPPORTED_LOCALES = ("en", "es", "pt-BR", "de", "fr", "ja", "ko", "hi", "id", "ar")

DEFAULT_PRIORITY_MAP = {
    "/": 1.0,
    "/pricing": 0.9,
    "/features": 0.9,
    "/about": 0.6,
    "/blog": 0.8,
    "/contact": 0.5,
    "/docs": 0.8,
}


@dataclass
class SitemapURL:
    """A single URL entry in the sitemap."""

    path: str
    lastmod: Optional[str] = None
    changefreq: str = "weekly"
    priority: float = 0.5
    hreflang: dict[str, str] = field(default_factory=dict)


class SitemapGenerator:
    """Generates sitemap.xml and robots.txt."""

    def __init__(
        self,
        site_url: str,
        priority_map: Optional[dict[str, float]] = None,
    ) -> None:
        self.site_url = site_url.rstrip("/")
        self.priority_map = priority_map or DEFAULT_PRIORITY_MAP
        self.urls: list[SitemapURL] = []

    def add_url(
        self,
        path: str,
        lastmod: Optional[str] = None,
        changefreq: str = "weekly",
        priority: Optional[float] = None,
        hreflang: Optional[dict[str, str]] = None,
    ) -> None:
        """Register a URL entry."""
        if not path.startswith("/"):
            path = "/" + path
        if priority is None:
            priority = self.priority_map.get(path, 0.5)
        priority = max(0.0, min(1.0, float(priority)))

        clean_hreflang: dict[str, str] = {}
        if hreflang:
            for locale, alt_path in hreflang.items():
                if locale not in SUPPORTED_LOCALES:
                    LOG.warning("unknown locale %s skipped", locale)
                    continue
                if not alt_path.startswith("/"):
                    alt_path = "/" + alt_path
                clean_hreflang[locale] = alt_path

        self.urls.append(
            SitemapURL(
                path=path,
                lastmod=lastmod or date.today().isoformat(),
                changefreq=changefreq,
                priority=priority,
                hreflang=clean_hreflang,
            )
        )

    def _url_block(self, entry: SitemapURL) -> str:
        full = f"{self.site_url}{entry.path}"
        parts = [
            "  <url>",
            f"    <loc>{escape(full)}</loc>",
            f"    <lastmod>{escape(entry.lastmod or date.today().isoformat())}</lastmod>",
            f"    <changefreq>{escape(entry.changefreq)}</changefreq>",
            f"    <priority>{entry.priority:.1f}</priority>",
        ]
        for locale in SUPPORTED_LOCALES:
            alt_path = entry.hreflang.get(locale)
            if alt_path:
                alt_url = f"{self.site_url}{alt_path}"
                parts.append(
                    f'    <xhtml:link rel="alternate" hreflang="{escape(locale)}" '
                    f'href="{escape(alt_url)}"/>'
                )
        if entry.hreflang:
            default_alt = entry.hreflang.get("en", entry.path)
            parts.append(
                f'    <xhtml:link rel="alternate" hreflang="x-default" '
                f'href="{escape(self.site_url + default_alt)}"/>'
            )
        parts.append("  </url>")
        return "\n".join(parts)

    def generate_xml(self, subset: Optional[list[SitemapURL]] = None) -> str:
        """Produce sitemap.xml contents."""
        urls = subset if subset is not None else self.urls
        header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        )
        body = "\n".join(self._url_block(u) for u in urls)
        return header + body + "\n</urlset>\n"

    def generate_sitemap_index(self, sub_sitemap_filenames: list[str]) -> str:
        """Produce a sitemap index XML referencing sub-sitemaps."""
        today = date.today().isoformat()
        header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        )
        blocks = []
        for name in sub_sitemap_filenames:
            loc = f"{self.site_url}/{name}"
            blocks.append(
                "  <sitemap>\n"
                f"    <loc>{escape(loc)}</loc>\n"
                f"    <lastmod>{today}</lastmod>\n"
                "  </sitemap>"
            )
        return header + "\n".join(blocks) + "\n</sitemapindex>\n"

    def generate_robots_txt(
        self,
        allow_paths: Optional[list[str]] = None,
        disallow_paths: Optional[list[str]] = None,
        sitemap_url: Optional[str] = None,
    ) -> str:
        """Produce robots.txt contents."""
        lines = ["User-agent: *"]
        if allow_paths:
            for p in allow_paths:
                lines.append(f"Allow: {p}")
        if disallow_paths:
            for p in disallow_paths:
                lines.append(f"Disallow: {p}")
        else:
            lines.append("Disallow:")

        lines.append("")
        final_sitemap = sitemap_url or f"{self.site_url}/sitemap.xml"
        lines.append(f"Sitemap: {final_sitemap}")
        lines.append("")
        return "\n".join(lines)

    def split_if_over_limit(self, max_urls: int = 50000) -> list[list[SitemapURL]]:
        """Split URL list into chunks, each under max_urls."""
        if len(self.urls) <= max_urls:
            return [self.urls]
        chunks: list[list[SitemapURL]] = []
        for i in range(0, len(self.urls), max_urls):
            chunks.append(self.urls[i : i + max_urls])
        return chunks

    def write_to_dir(
        self,
        out_dir: str,
        allow_paths: Optional[list[str]] = None,
        disallow_paths: Optional[list[str]] = None,
        max_urls: int = 50000,
    ) -> dict[str, str]:
        """Write sitemap.xml (or index + parts) and robots.txt to out_dir."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)

        written: dict[str, str] = {}
        chunks = self.split_if_over_limit(max_urls=max_urls)

        if len(chunks) == 1:
            path = out / "sitemap.xml"
            path.write_text(self.generate_xml(chunks[0]), encoding="utf-8")
            written["sitemap.xml"] = str(path)
            sitemap_url = f"{self.site_url}/sitemap.xml"
        else:
            filenames = []
            for idx, chunk in enumerate(chunks, start=1):
                name = f"sitemap_{idx}.xml"
                path = out / name
                path.write_text(self.generate_xml(chunk), encoding="utf-8")
                written[name] = str(path)
                filenames.append(name)
            index_path = out / "sitemap.xml"
            index_path.write_text(self.generate_sitemap_index(filenames), encoding="utf-8")
            written["sitemap.xml"] = str(index_path)
            sitemap_url = f"{self.site_url}/sitemap.xml"

        robots_path = out / "robots.txt"
        robots_path.write_text(
            self.generate_robots_txt(
                allow_paths=allow_paths,
                disallow_paths=disallow_paths,
                sitemap_url=sitemap_url,
            ),
            encoding="utf-8",
        )
        written["robots.txt"] = str(robots_path)
        return written


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Generate sitemap.xml and robots.txt")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    gen = SitemapGenerator(site_url=manifest["site_url"])
    for url in manifest.get("urls", []):
        gen.add_url(
            path=url["path"],
            lastmod=url.get("lastmod"),
            changefreq=url.get("changefreq", "weekly"),
            priority=url.get("priority"),
            hreflang=url.get("hreflang"),
        )
    robots = manifest.get("robots", {})
    written = gen.write_to_dir(
        out_dir=args.out,
        allow_paths=robots.get("allow"),
        disallow_paths=robots.get("disallow"),
    )
    for name, path in written.items():
        LOG.info("wrote %s -> %s", name, path)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.exit(_cli())
