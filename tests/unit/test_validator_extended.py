"""Extended validator tests for 100% coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock

from national_treasure.services.browser.validator import (
    ResponseValidator,
    validate_response,
    BLOCK_PATTERNS,
    CAPTCHA_PATTERNS,
    RATE_LIMIT_PATTERNS,
)
from national_treasure.core.models import ValidationResult


class TestResponseValidatorEdgeCases:
    """Test edge cases in response validation."""

    @pytest.mark.asyncio
    async def test_validate_response_exception(self):
        """Should handle exception during validation."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(side_effect=Exception("Content failed"))

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        # Should indicate blocked due to content error
        assert isinstance(result, ValidationResult)
        assert result.blocked is True
        assert result.reason == "content_error"

    @pytest.mark.asyncio
    async def test_validate_none_response(self):
        """Should handle None response."""
        page = MagicMock()
        page.content = AsyncMock(return_value="<html></html>")

        validator = ResponseValidator()
        result = await validator.validate(None, page)

        # Should indicate blocked due to no response
        assert result.blocked is True
        assert result.reason == "navigation_failed"


class TestValidateResponseFunction:
    """Test the validate_response helper function."""

    @pytest.mark.asyncio
    async def test_validate_response_helper(self):
        """Should use helper function correctly."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html><body>Normal page content here</body></html>")

        result = await validate_response(response, page)
        assert isinstance(result, ValidationResult)


class TestBlockPatternMatching:
    """Test block pattern matching."""

    @pytest.mark.asyncio
    async def test_cloudflare_detection(self):
        """Should detect Cloudflare by content."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Just a moment... checking your browser</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)
        assert result.blocked is True
        assert result.reason == "cloudflare"

    @pytest.mark.asyncio
    async def test_captcha_detection(self):
        """Should detect captcha patterns."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Please complete the captcha to continue</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)
        assert result.blocked is True

    @pytest.mark.asyncio
    async def test_rate_limit_detection(self):
        """Should detect rate limiting by status."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=429)
        page = MagicMock()
        page.content = AsyncMock(return_value="Too many requests")

        validator = ResponseValidator()
        result = await validator.validate(response, page)
        assert result.blocked is True
        assert "429" in result.reason


class TestValidatorStatus:
    """Test validation of different status codes."""

    @pytest.mark.asyncio
    async def test_validate_403_status(self):
        """Should handle 403 forbidden."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=403)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Forbidden</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is True
        assert "403" in result.reason

    @pytest.mark.asyncio
    async def test_validate_429_status(self):
        """Should handle 429 too many requests."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=429)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Rate limited</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is True

    @pytest.mark.asyncio
    async def test_validate_503_status(self):
        """Should handle 503 service unavailable."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=503)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Service unavailable</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is True

    @pytest.mark.asyncio
    async def test_validate_200_normal(self):
        """Should pass valid 200 response."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html><body><h1>Welcome</h1><p>Content here that is real</p></body></html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is False


class TestCustomPatterns:
    """Test custom block patterns."""

    @pytest.mark.asyncio
    async def test_custom_block_pattern(self):
        """Should detect custom block patterns."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>CUSTOM BLOCK MESSAGE HERE</html>")

        validator = ResponseValidator(custom_block_patterns=["custom block message"])
        result = await validator.validate(response, page)

        assert result.blocked is True
        assert result.reason == "custom_block"

    @pytest.mark.asyncio
    async def test_custom_success_pattern(self):
        """Should allow custom success patterns to bypass blocks."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        # Content has cloudflare pattern but also success pattern
        page.content = AsyncMock(return_value="<html>Just a moment SUCCESS_MARKER</html>")

        validator = ResponseValidator(custom_success_patterns=["success_marker"])
        result = await validator.validate(response, page)

        assert result.blocked is False


class TestMinContentLength:
    """Test minimum content length validation."""

    @pytest.mark.asyncio
    async def test_short_content(self):
        """Should allow short content if no blocks detected."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        page = MagicMock()
        page.content = AsyncMock(return_value="<html>OK</html>")

        validator = ResponseValidator(min_content_length=10)
        result = await validator.validate(response, page)

        # Short content alone doesn't block
        assert isinstance(result, ValidationResult)
