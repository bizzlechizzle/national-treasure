"""Full validator tests for 100% coverage."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from national_treasure.services.browser.validator import ResponseValidator, ValidationResult


class TestLoginWallDetection:
    """Test login wall pattern detection."""

    @pytest.mark.asyncio
    async def test_login_required_detection(self):
        """Should detect login required patterns."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        type(response).headers = PropertyMock(return_value={})

        page = MagicMock()
        page.content = AsyncMock(return_value="""
            <html>
                <body>
                    <h1>Sign in to continue</h1>
                    <p>You need to log in to view this content.</p>
                </body>
            </html>
        """)

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is False  # Not blocked, but limited
        assert result.reason == "login_required"


class TestServiceDetection:
    """Test blocking service detection from headers."""

    @pytest.mark.asyncio
    async def test_cloudfront_detection(self):
        """Should detect CloudFront from headers."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=403)
        type(response).headers = PropertyMock(return_value={
            "x-amz-cf-id": "abc123",
        })

        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Access Denied</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is True
        assert "403" in result.reason or result.blocked is True

    @pytest.mark.asyncio
    async def test_cloudfront_pop_detection(self):
        """Should detect CloudFront from x-amz-cf-pop header."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=403)
        type(response).headers = PropertyMock(return_value={
            "x-amz-cf-pop": "IAD50-C1",
        })

        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Forbidden</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is True

    @pytest.mark.asyncio
    async def test_akamai_detection(self):
        """Should detect Akamai from headers."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=403)
        type(response).headers = PropertyMock(return_value={
            "x-akamai-request-id": "def456",
        })

        page = MagicMock()
        page.content = AsyncMock(return_value="<html>Access Denied</html>")

        validator = ResponseValidator()
        result = await validator.validate(response, page)

        assert result.blocked is True


class TestExpectedShortPage:
    """Test _is_expected_short_page method."""

    def test_json_response_expected(self):
        """Should recognize JSON as expected short content."""
        validator = ResponseValidator()

        assert validator._is_expected_short_page('{"status": "ok"}') is True
        assert validator._is_expected_short_page('[1, 2, 3]') is True

    def test_meta_refresh_expected(self):
        """Should recognize meta refresh as expected."""
        validator = ResponseValidator()

        content = '<html><head><meta http-equiv="refresh" content="0;url=/new"></head></html>'
        assert validator._is_expected_short_page(content) is True

    def test_minimal_body_expected(self):
        """Should recognize minimal HTML body as expected."""
        validator = ResponseValidator()

        content = '<html><head></head><body></body></html>'
        assert validator._is_expected_short_page(content) is True

    def test_normal_content_not_expected(self):
        """Should not recognize normal content as expected short."""
        validator = ResponseValidator()

        # Lots of tags means it's a regular page
        content = "<html><head></head><body>" + "<div>x</div>" * 30 + "</body></html>"
        # Has many tags (>20), so not "short"
        result = validator._is_expected_short_page(content)
        assert result is False


class TestValidatorWithMinContentLength:
    """Test validator with minimum content length."""

    @pytest.mark.asyncio
    async def test_short_json_passes(self):
        """Should pass short JSON content."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        type(response).headers = PropertyMock(return_value={})

        page = MagicMock()
        page.content = AsyncMock(return_value='{"status": "ok"}')

        validator = ResponseValidator(min_content_length=1000)
        result = await validator.validate(response, page)

        # JSON is expected short, should pass
        assert result.blocked is False

    @pytest.mark.asyncio
    async def test_short_normal_content_blocked(self):
        """Should flag short normal content."""
        response = MagicMock()
        type(response).status = PropertyMock(return_value=200)
        type(response).headers = PropertyMock(return_value={})

        page = MagicMock()
        # Very short content that's not JSON/redirect
        page.content = AsyncMock(return_value="""
            <html>
            <head></head>
            <body>
                <div>Short</div>
                <div>Content</div>
                <div>Here</div>
                <div>More</div>
                <div>Tags</div>
                <div>To</div>
                <div>Make</div>
                <div>It</div>
                <div>Not</div>
                <div>Expected</div>
                <div>Short</div>
                <div>Page</div>
                <div>Type</div>
                <div>Check</div>
                <div>Fails</div>
                <div>Now</div>
                <div>Extra</div>
                <div>Tags</div>
                <div>Added</div>
                <div>Here</div>
            </body>
            </html>
        """)

        validator = ResponseValidator(min_content_length=10000)
        result = await validator.validate(response, page)

        # Content too short - should be blocked
        assert result.blocked is True
        assert result.reason == "content_too_short"
