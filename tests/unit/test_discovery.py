"""Tests for image discovery."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from national_treasure.services.image.discovery import (
    DiscoveredImage,
    ImageDiscoveryResult,
    parse_srcset,
    discover_images,
    discover_and_deduplicate,
    _extract_schema_images,
)


class TestDiscoveredImage:
    """Test DiscoveredImage dataclass."""

    def test_basic_image(self):
        """Should create image with required fields."""
        img = DiscoveredImage(
            url="https://example.com/image.jpg",
            source="img",
        )

        assert img.url == "https://example.com/image.jpg"
        assert img.source == "img"
        assert img.alt is None
        assert img.priority == 0

    def test_full_image(self):
        """Should create image with all fields."""
        img = DiscoveredImage(
            url="https://example.com/image.jpg",
            source="srcset",
            alt="Test image",
            title="Title",
            width=800,
            height=600,
            srcset_descriptor="2x",
            priority=5,
        )

        assert img.width == 800
        assert img.height == 600
        assert img.srcset_descriptor == "2x"
        assert img.priority == 5


class TestImageDiscoveryResult:
    """Test ImageDiscoveryResult dataclass."""

    def test_empty_result(self):
        """Should create empty result."""
        result = ImageDiscoveryResult()

        assert result.images == []
        assert result.page_url == ""
        assert result.total_found == 0

    def test_with_images(self):
        """Should store images correctly."""
        images = [
            DiscoveredImage(url="https://example.com/1.jpg", source="img"),
            DiscoveredImage(url="https://example.com/2.jpg", source="og"),
        ]

        result = ImageDiscoveryResult(
            images=images,
            page_url="https://example.com",
            total_found=2,
        )

        assert len(result.images) == 2
        assert result.total_found == 2


class TestParseSrcset:
    """Test srcset parsing."""

    def test_empty_srcset(self):
        """Should handle empty srcset."""
        result = parse_srcset("", "https://example.com")
        assert result == []

    def test_none_srcset(self):
        """Should handle None srcset."""
        result = parse_srcset(None, "https://example.com")
        assert result == []

    def test_simple_srcset(self):
        """Should parse simple srcset."""
        srcset = "image.jpg 1x, image@2x.jpg 2x"
        result = parse_srcset(srcset, "https://example.com/")

        assert len(result) == 2
        assert result[0].url == "https://example.com/image.jpg"
        assert result[0].srcset_descriptor == "1x"
        assert result[1].url == "https://example.com/image@2x.jpg"
        assert result[1].srcset_descriptor == "2x"

    def test_width_descriptor(self):
        """Should parse width descriptors."""
        srcset = "small.jpg 400w, large.jpg 800w"
        result = parse_srcset(srcset, "https://example.com/")

        assert len(result) == 2
        assert result[0].width == 400
        assert result[0].srcset_descriptor == "400w"
        assert result[1].width == 800

    def test_absolute_urls(self):
        """Should handle absolute URLs in srcset."""
        srcset = "https://cdn.example.com/img.jpg 1x"
        result = parse_srcset(srcset, "https://example.com/")

        assert len(result) == 1
        assert result[0].url == "https://cdn.example.com/img.jpg"

    def test_srcset_priority(self):
        """Srcset images should have priority 2."""
        srcset = "image.jpg 1x"
        result = parse_srcset(srcset, "https://example.com/")

        assert result[0].priority == 2


class TestExtractSchemaImages:
    """Test Schema.org JSON-LD extraction."""

    def test_string_image(self):
        """Should extract string image URL."""
        data = {"image": "https://example.com/image.jpg"}
        result = _extract_schema_images(data, "https://example.com")

        assert len(result) == 1
        assert result[0].url == "https://example.com/image.jpg"
        assert result[0].source == "schema"

    def test_object_image(self):
        """Should extract image object with URL."""
        data = {
            "image": {
                "url": "https://example.com/image.jpg",
                "width": 800,
                "height": 600,
            }
        }
        result = _extract_schema_images(data, "https://example.com")

        assert len(result) == 1
        assert result[0].width == 800
        assert result[0].height == 600

    def test_array_images(self):
        """Should extract array of images."""
        data = {
            "image": [
                "https://example.com/1.jpg",
                "https://example.com/2.jpg",
            ]
        }
        result = _extract_schema_images(data, "https://example.com")

        assert len(result) == 2

    def test_graph_images(self):
        """Should extract images from @graph."""
        data = {
            "@graph": [
                {"image": "https://example.com/1.jpg"},
                {"image": "https://example.com/2.jpg"},
            ]
        }
        result = _extract_schema_images(data, "https://example.com")

        assert len(result) == 2

    def test_nested_images(self):
        """Should extract nested images."""
        data = {
            "mainEntity": {
                "image": "https://example.com/nested.jpg"
            }
        }
        result = _extract_schema_images(data, "https://example.com")

        assert len(result) == 1

    def test_relative_urls(self):
        """Should resolve relative URLs."""
        data = {"image": "/images/photo.jpg"}
        result = _extract_schema_images(data, "https://example.com")

        assert result[0].url == "https://example.com/images/photo.jpg"


class MockPage:
    """Mock Playwright Page for testing."""

    def __init__(
        self,
        url: str = "https://example.com",
        img_data: list = None,
        og_data: list = None,
        twitter_data: list = None,
        schema_data: list = None,
        picture_data: list = None,
        bg_data: list = None,
    ):
        self._url = url
        self._img_data = img_data or []
        self._og_data = og_data or []
        self._twitter_data = twitter_data or []
        self._schema_data = schema_data or []
        self._picture_data = picture_data or []
        self._bg_data = bg_data or []
        self._call_count = 0

    @property
    def url(self):
        return self._url

    async def evaluate(self, script):
        """Return mock data based on script content."""
        self._call_count += 1

        if "querySelectorAll('img')" in script:
            return self._img_data
        elif 'meta[property^="og:image"]' in script:
            return self._og_data
        elif 'meta[name^="twitter:image"]' in script:
            return self._twitter_data
        elif 'script[type="application/ld+json"]' in script:
            return self._schema_data
        elif "picture source" in script:
            return self._picture_data
        elif "background-image" in script:
            return self._bg_data

        return []


class TestDiscoverImages:
    """Test image discovery from page."""

    @pytest.mark.asyncio
    async def test_empty_page(self):
        """Should handle page with no images."""
        page = MockPage()
        result = await discover_images(page)

        assert result.total_found == 0
        assert result.page_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_img_tags(self):
        """Should discover img tag images."""
        page = MockPage(
            img_data=[
                {
                    "src": "https://example.com/photo.jpg",
                    "alt": "Photo",
                    "width": 800,
                    "height": 600,
                }
            ]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].url == "https://example.com/photo.jpg"
        assert result.images[0].source == "img"
        assert result.images[0].alt == "Photo"

    @pytest.mark.asyncio
    async def test_srcset_parsing(self):
        """Should parse srcset from img tags."""
        page = MockPage(
            img_data=[
                {
                    "src": "https://example.com/photo.jpg",
                    "srcset": "https://example.com/photo@2x.jpg 2x",
                    "alt": "Photo",
                }
            ]
        )

        result = await discover_images(page)

        # Should have both src and srcset images
        assert result.total_found == 2
        sources = [img.source for img in result.images]
        assert "img" in sources
        assert "srcset" in sources

    @pytest.mark.asyncio
    async def test_lazy_loading_data_src(self):
        """Should discover lazy-loaded images."""
        page = MockPage(
            img_data=[
                {
                    "src": "",
                    "dataSrc": "https://example.com/lazy.jpg",
                }
            ]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].source == "data"

    @pytest.mark.asyncio
    async def test_og_images(self):
        """Should discover Open Graph images."""
        page = MockPage(
            og_data=[
                {"content": "https://example.com/og.jpg", "property": "og:image"}
            ]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].source == "og"
        assert result.images[0].priority == 5

    @pytest.mark.asyncio
    async def test_twitter_images(self):
        """Should discover Twitter card images."""
        page = MockPage(
            twitter_data=["https://example.com/twitter.jpg"]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].source == "twitter"

    @pytest.mark.asyncio
    async def test_schema_images(self):
        """Should discover Schema.org images."""
        page = MockPage(
            schema_data=['{"image": "https://example.com/schema.jpg"}']
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].source == "schema"

    @pytest.mark.asyncio
    async def test_picture_sources(self):
        """Should discover picture element sources."""
        page = MockPage(
            picture_data=[
                {"srcset": "https://example.com/webp.webp 1x", "type": "image/webp"}
            ]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].source == "picture"

    @pytest.mark.asyncio
    async def test_background_images(self):
        """Should discover CSS background images."""
        page = MockPage(
            bg_data=["https://example.com/bg.jpg"]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].source == "css"
        assert result.images[0].priority == 1

    @pytest.mark.asyncio
    async def test_deduplication(self):
        """Should not include duplicate URLs."""
        page = MockPage(
            img_data=[
                {"src": "https://example.com/photo.jpg"},
                {"src": "https://example.com/photo.jpg"},
            ]
        )

        result = await discover_images(page)

        # Should only have one despite two img tags
        assert result.total_found == 1

    @pytest.mark.asyncio
    async def test_priority_sorting(self):
        """Should sort by priority (highest first)."""
        page = MockPage(
            bg_data=["https://example.com/bg.jpg"],  # priority 1
            og_data=[
                {"content": "https://example.com/og.jpg", "property": "og:image"}
            ],  # priority 5
        )

        result = await discover_images(page)

        assert result.total_found == 2
        assert result.images[0].source == "og"  # Higher priority first
        assert result.images[1].source == "css"

    @pytest.mark.asyncio
    async def test_filters_non_http(self):
        """Should filter non-http URLs."""
        page = MockPage(
            img_data=[
                {"src": "data:image/png;base64,abc"},
                {"src": "blob:abc"},
                {"src": "https://example.com/real.jpg"},
            ]
        )

        result = await discover_images(page)

        assert result.total_found == 1
        assert result.images[0].url == "https://example.com/real.jpg"


class TestDiscoverAndDeduplicate:
    """Test deduplication by normalized URL."""

    @pytest.mark.asyncio
    async def test_removes_query_params(self):
        """Should deduplicate URLs differing only in query params."""
        page = MockPage(
            img_data=[
                {"src": "https://example.com/photo.jpg?v=1"},
                {"src": "https://example.com/photo.jpg?v=2"},
            ]
        )

        result = await discover_and_deduplicate(page)

        # Should only have one (first encountered with higher priority wins)
        assert len(result) == 1
        assert "photo.jpg" in result[0].url

    @pytest.mark.asyncio
    async def test_keeps_higher_priority(self):
        """Should keep higher priority version when deduplicating."""
        page = MockPage(
            bg_data=["https://example.com/image.jpg"],  # priority 1
            og_data=[
                {"content": "https://example.com/image.jpg", "property": "og:image"}
            ],  # priority 5
        )

        result = await discover_and_deduplicate(page)

        assert len(result) == 1
        assert result[0].priority == 5  # OG has higher priority
