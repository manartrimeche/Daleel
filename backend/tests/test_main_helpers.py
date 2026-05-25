"""Tests for main.py — pure helper functions."""

from unittest.mock import MagicMock
from fastapi import Request
from starlette.responses import JSONResponse

from app.main import _rate_limit_handler, _find_interface_dir


class TestFindInterfaceDir:
    def test_returns_path(self):
        result = _find_interface_dir()
        assert result is not None
        assert "interface-daleel" in str(result) or "static" in str(result)

    def test_returns_pathlib_path(self):
        from pathlib import Path
        result = _find_interface_dir()
        assert isinstance(result, Path)


class TestRateLimitHandler:
    def _make_exc(self, headers):
        exc = MagicMock()
        exc.headers = headers
        return exc

    def test_with_retry_after(self):
        request = MagicMock(spec=Request)
        exc = self._make_exc({"Retry-After": "60"})
        response = _rate_limit_handler(request, exc)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 429

    def test_without_retry_after(self):
        request = MagicMock(spec=Request)
        exc = self._make_exc({})
        response = _rate_limit_handler(request, exc)
        assert response.status_code == 429

    def test_none_headers(self):
        request = MagicMock(spec=Request)
        exc = self._make_exc(None)
        response = _rate_limit_handler(request, exc)
        assert response.status_code == 429
