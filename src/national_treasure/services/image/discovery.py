"""Image discovery for National Treasure.

Discovers all images on a page from multiple sources:
- <img> tags (src, srcset, data-src)
- Open Graph meta tags
- Schema.org JSON-LD
- CSS background images
- data-* attributes
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page


@dataclass
class DiscoveredImage:
    """An image discovered on a page."""
    url: str
    source: str  # img, srcset, og, schema, css, data
    alt: str | None = None
    title: str | None = None
    width: int | None = None
    height: int | None = None
    srcset_descriptor: str | None = None  # e.g., "2x" or "800w"
    priority: int = 0  # Higher = more important


@dataclass
class ImageDiscoveryResult:
    """Result of image discovery."""
    images: list[DiscoveredImage] = field(default_factory=list)
    page_url: str = ""
    total_found: int = 0


def parse_srcset(srcset: str, base_url: str) -> list[DiscoveredImage]:
    """Parse srcset attribute into individual image entries.

    Args:
        srcset: srcset attribute value
        base_url: Base URL for resolving relative URLs

    Returns:
        List of DiscoveredImage objects
    """
    images = []
    if not srcset:
        return images

    # Split by comma, handling URLs with commas
    parts = re.split(r',\s*(?=\S+\s+\d)', srcset)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Split into URL and descriptor
        match = re.match(r'(\S+)\s*(.*)', part)
        if match:
            url = match.group(1)
            descriptor = match.group(2).strip() or None

            # Resolve relative URL
            full_url = urljoin(base_url, url)

            # Parse descriptor for width
            width = None
            if descriptor and descriptor.endswith('w'):
                try:
                    width = int(descriptor[:-1])
                except ValueError:
                    pass

            images.append(DiscoveredImage(
                url=full_url,
                source="srcset",
                srcset_descriptor=descriptor,
                width=width,
                priority=2,  # srcset images often higher quality
            ))

    return images


async def discover_images(page: Page) -> ImageDiscoveryResult:
    """Discover all images on a page.

    Args:
        page: Playwright Page object

    Returns:
        ImageDiscoveryResult with all found images
    """
    result = ImageDiscoveryResult()
    result.page_url = page.url
    seen_urls: set[str] = set()

    def add_image(img: DiscoveredImage) -> None:
        """Add image if not already seen."""
        if img.url and img.url not in seen_urls and img.url.startswith("http"):
            seen_urls.add(img.url)
            result.images.append(img)

    # 1. Standard <img> tags
    img_data = await page.evaluate("""
        () => Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src,
            srcset: img.srcset,
            dataSrc: img.dataset.src,
            dataLazySrc: img.dataset.lazySrc,
            dataOriginal: img.dataset.original,
            alt: img.alt,
            title: img.title,
            width: img.naturalWidth || img.width,
            height: img.naturalHeight || img.height,
        }))
    """)

    for img in img_data:
        # Main src
        if img.get("src"):
            add_image(DiscoveredImage(
                url=urljoin(result.page_url, img["src"]),
                source="img",
                alt=img.get("alt"),
                title=img.get("title"),
                width=img.get("width"),
                height=img.get("height"),
                priority=3,
            ))

        # Parse srcset
        if img.get("srcset"):
            for srcset_img in parse_srcset(img["srcset"], result.page_url):
                srcset_img.alt = img.get("alt")
                add_image(srcset_img)

        # data-src variants (lazy loading)
        for data_key in ["dataSrc", "dataLazySrc", "dataOriginal"]:
            if img.get(data_key):
                add_image(DiscoveredImage(
                    url=urljoin(result.page_url, img[data_key]),
                    source="data",
                    alt=img.get("alt"),
                    priority=2,
                ))

    # 2. Open Graph images
    og_images = await page.evaluate("""
        () => Array.from(document.querySelectorAll('meta[property^="og:image"]'))
            .map(meta => ({
                content: meta.content,
                property: meta.getAttribute('property'),
            }))
    """)

    for og in og_images:
        if og.get("content"):
            priority = 5 if og.get("property") == "og:image" else 4
            add_image(DiscoveredImage(
                url=urljoin(result.page_url, og["content"]),
                source="og",
                priority=priority,
            ))

    # 3. Twitter card images
    twitter_images = await page.evaluate("""
        () => Array.from(document.querySelectorAll('meta[name^="twitter:image"]'))
            .map(meta => meta.content)
    """)

    for url in twitter_images:
        if url:
            add_image(DiscoveredImage(
                url=urljoin(result.page_url, url),
                source="twitter",
                priority=4,
            ))

    # 4. Schema.org JSON-LD
    schema_scripts = await page.evaluate("""
        () => Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
            .map(s => s.textContent)
    """)

    for script in schema_scripts:
        try:
            data = json.loads(script)
            schema_images = _extract_schema_images(data, result.page_url)
            for img in schema_images:
                add_image(img)
        except (json.JSONDecodeError, TypeError):
            continue

    # 5. <picture> sources
    picture_sources = await page.evaluate("""
        () => Array.from(document.querySelectorAll('picture source')).map(s => ({
            srcset: s.srcset,
            media: s.media,
            type: s.type,
        }))
    """)

    for source in picture_sources:
        if source.get("srcset"):
            for img in parse_srcset(source["srcset"], result.page_url):
                img.source = "picture"
                add_image(img)

    # 6. Background images (limited to obvious ones)
    bg_images = await page.evaluate("""
        () => {
            const images = [];
            const elements = document.querySelectorAll('[style*="background-image"]');
            elements.forEach(el => {
                const style = el.getAttribute('style') || '';
                const match = style.match(/background-image:\\s*url\\(['"]?([^'"\\)]+)['"]?\\)/);
                if (match) images.push(match[1]);
            });
            return images;
        }
    """)

    for url in bg_images:
        if url:
            add_image(DiscoveredImage(
                url=urljoin(result.page_url, url),
                source="css",
                priority=1,
            ))

    # Sort by priority (highest first)
    result.images.sort(key=lambda x: -x.priority)
    result.total_found = len(result.images)

    return result


def _extract_schema_images(data: Any, base_url: str) -> list[DiscoveredImage]:
    """Extract images from Schema.org JSON-LD data.

    Args:
        data: Parsed JSON-LD data
        base_url: Base URL for resolving relative URLs

    Returns:
        List of DiscoveredImage objects
    """
    images = []

    def process_item(item: Any) -> None:
        if isinstance(item, dict):
            # Check for image property
            if "image" in item:
                img = item["image"]
                if isinstance(img, str):
                    images.append(DiscoveredImage(
                        url=urljoin(base_url, img),
                        source="schema",
                        priority=4,
                    ))
                elif isinstance(img, dict) and "url" in img:
                    images.append(DiscoveredImage(
                        url=urljoin(base_url, img["url"]),
                        source="schema",
                        width=img.get("width"),
                        height=img.get("height"),
                        priority=4,
                    ))
                elif isinstance(img, list):
                    for i in img:
                        if isinstance(i, str):
                            images.append(DiscoveredImage(
                                url=urljoin(base_url, i),
                                source="schema",
                                priority=4,
                            ))

            # Check for @graph
            if "@graph" in item:
                for graph_item in item["@graph"]:
                    process_item(graph_item)

            # Recurse into other dict values (skip @graph as it's handled above)
            for key, value in item.items():
                if key != "@graph" and isinstance(value, (dict, list)):
                    process_item(value)

        elif isinstance(item, list):
            for i in item:
                process_item(i)

    process_item(data)
    return images


async def discover_and_deduplicate(page: Page) -> list[DiscoveredImage]:
    """Discover images and return deduplicated list by normalized URL.

    Args:
        page: Playwright Page object

    Returns:
        Deduplicated list of images, highest priority first
    """
    result = await discover_images(page)

    # Further deduplicate by removing query params and fragments
    seen_base_urls: dict[str, DiscoveredImage] = {}

    for img in result.images:
        parsed = urlparse(img.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if base_url not in seen_base_urls or img.priority > seen_base_urls[base_url].priority:
            seen_base_urls[base_url] = img

    return list(seen_base_urls.values())
