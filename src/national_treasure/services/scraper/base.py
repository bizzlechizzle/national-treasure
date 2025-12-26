"""Base scraper with selector training integration."""

import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Page

from national_treasure.services.scraper.training import TrainingService


class BaseScraper(ABC):
    """Abstract base class for site-specific scrapers.

    Provides common extraction helpers with automatic training feedback.
    """

    # Override in subclass
    SITE_PATTERNS: list[str] = []  # URL patterns this scraper handles
    SELECTORS: dict[str, list[str]] = {}  # Field -> fallback selectors

    def __init__(self, training_service: TrainingService | None = None):
        """Initialize scraper.

        Args:
            training_service: Optional training service for feedback
        """
        self.training = training_service
        self._site = self._get_site_name()

    def _get_site_name(self) -> str:
        """Get site name from class patterns."""
        if self.SITE_PATTERNS:
            # Extract domain from first pattern
            pattern = self.SITE_PATTERNS[0]
            # Remove regex parts
            pattern = pattern.replace(".*", "").replace("^", "").replace("$", "")
            parsed = urlparse(f"https://{pattern}")
            return parsed.netloc or pattern
        return self.__class__.__name__.lower().replace("scraper", "")

    @classmethod
    def matches_url(cls, url: str) -> bool:
        """Check if this scraper handles the given URL.

        Args:
            url: URL to check

        Returns:
            True if scraper handles this URL
        """
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in cls.SITE_PATTERNS)

    @abstractmethod
    async def extract(self, page: Page, url: str) -> dict[str, Any]:
        """Extract data from page.

        Args:
            page: Playwright page
            url: Page URL

        Returns:
            Extracted data dict
        """
        pass

    async def extract_text(
        self,
        page: Page,
        field: str,
        selectors: list[str] | None = None,
        required: bool = False,
    ) -> str | None:
        """Extract text using selectors with fallback chain.

        Args:
            page: Playwright page
            field: Field name for training
            selectors: Selectors to try (uses SELECTORS[field] if None)
            required: Whether to raise if not found

        Returns:
            Extracted text or None
        """
        selectors = selectors or self.SELECTORS.get(field, [])

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.strip() if text else None
                    if text:
                        # Record success
                        if self.training:
                            await self.training.record_selector_outcome(
                                self._site, field, selector, True, text
                            )
                        return text
                    else:
                        # Empty result
                        if self.training:
                            await self.training.record_selector_outcome(
                                self._site, field, selector, False
                            )
            except Exception:
                # Record failure
                if self.training:
                    await self.training.record_selector_outcome(
                        self._site, field, selector, False
                    )

        if required:
            raise ValueError(f"Could not extract required field: {field}")

        return None

    async def extract_attribute(
        self,
        page: Page,
        field: str,
        attribute: str,
        selectors: list[str] | None = None,
        required: bool = False,
    ) -> str | None:
        """Extract attribute value using selectors with fallback chain.

        Args:
            page: Playwright page
            field: Field name for training
            attribute: Attribute to extract (e.g., "href", "src")
            selectors: Selectors to try
            required: Whether to raise if not found

        Returns:
            Extracted attribute value or None
        """
        selectors = selectors or self.SELECTORS.get(field, [])

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    value = await element.get_attribute(attribute)
                    if value:
                        if self.training:
                            await self.training.record_selector_outcome(
                                self._site, field, selector, True, value
                            )
                        return value
                    else:
                        if self.training:
                            await self.training.record_selector_outcome(
                                self._site, field, selector, False
                            )
            except Exception:
                if self.training:
                    await self.training.record_selector_outcome(
                        self._site, field, selector, False
                    )

        if required:
            raise ValueError(f"Could not extract required field: {field}")

        return None

    async def extract_all_text(
        self,
        page: Page,
        field: str,
        selectors: list[str] | None = None,
    ) -> list[str]:
        """Extract text from all matching elements.

        Args:
            page: Playwright page
            field: Field name for training
            selectors: Selectors to try

        Returns:
            List of extracted text values
        """
        selectors = selectors or self.SELECTORS.get(field, [])
        results = []

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and text.strip():
                        results.append(text.strip())

                if results:
                    if self.training:
                        await self.training.record_selector_outcome(
                            self._site, field, selector, True, str(len(results))
                        )
                    break
            except Exception:
                continue

        return results

    async def extract_with_js(
        self,
        page: Page,
        field: str,
        js_expression: str,
    ) -> Any:
        """Extract data using JavaScript evaluation.

        Args:
            page: Playwright page
            field: Field name for training
            js_expression: JavaScript to evaluate

        Returns:
            Result of JavaScript evaluation
        """
        try:
            result = await page.evaluate(js_expression)
            if result and self.training:
                await self.training.record_selector_outcome(
                    self._site, field, f"js:{js_expression[:50]}", True, str(result)[:100]
                )
            return result
        except Exception:
            if self.training:
                await self.training.record_selector_outcome(
                    self._site, field, f"js:{js_expression[:50]}", False
                )
            return None

    async def extract_json_ld(self, page: Page) -> dict[str, Any] | None:
        """Extract JSON-LD structured data from page.

        Args:
            page: Playwright page

        Returns:
            Parsed JSON-LD data or None
        """
        try:
            result = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const script of scripts) {
                        try {
                            return JSON.parse(script.textContent);
                        } catch (e) {}
                    }
                    return null;
                }
            """)
            return result
        except Exception:
            return None

    async def extract_meta_tags(self, page: Page) -> dict[str, str]:
        """Extract common meta tags from page.

        Args:
            page: Playwright page

        Returns:
            Dict of meta tag values
        """
        try:
            result = await page.evaluate("""
                () => {
                    const meta = {};
                    const tags = [
                        ['og:title', 'property'],
                        ['og:description', 'property'],
                        ['og:image', 'property'],
                        ['og:url', 'property'],
                        ['og:type', 'property'],
                        ['twitter:title', 'name'],
                        ['twitter:description', 'name'],
                        ['twitter:image', 'name'],
                        ['description', 'name'],
                        ['author', 'name'],
                        ['keywords', 'name'],
                    ];

                    for (const [name, attr] of tags) {
                        const el = document.querySelector(`meta[${attr}="${name}"]`);
                        if (el) {
                            meta[name] = el.getAttribute('content');
                        }
                    }

                    return meta;
                }
            """)
            return result or {}
        except Exception:
            return {}
