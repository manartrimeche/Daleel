"""
Unit tests for _call_ollama retry/backoff behaviour.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from app.services.llm_service import _call_ollama, _backoff_delay


class TestBackoffDelay(unittest.TestCase):
    def test_increases_exponentially(self):
        # Without jitter component, base * 2^attempt
        base_delays = [1.0 * (2 ** i) for i in range(5)]
        self.assertEqual(base_delays, [1.0, 2.0, 4.0, 8.0, 16.0])

    def test_capped_at_maximum(self):
        for _ in range(100):
            d = _backoff_delay(20, 1.0, 16.0)
            self.assertLessEqual(d, 16.0 * 1.25 + 0.01)

    def test_always_positive(self):
        for attempt in range(10):
            d = _backoff_delay(attempt, 0.5, 10.0)
            self.assertGreater(d, 0)


class TestCallOllamaRetry(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    @patch("app.services.llm_service.get_settings")
    @patch("httpx.AsyncClient.post")
    def test_success_on_first_try(self, mock_post, mock_settings):
        settings = MagicMock()
        settings.llm_max_retries = 3
        settings.llm_timeout_connect = 10.0
        settings.llm_timeout_read = 60.0
        settings.llm_backoff_base = 1.0
        settings.llm_backoff_max = 16.0
        mock_settings.return_value = settings

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        result = self._run(_call_ollama("model", [{"role": "user", "content": "hi"}], 0.5))
        self.assertEqual(result, "Test response")
        self.assertEqual(mock_post.call_count, 1)

    @patch("app.services.llm_service.get_settings")
    @patch("app.services.llm_service.asyncio.sleep", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    def test_retries_on_connect_error(self, mock_post, mock_sleep, mock_settings):
        settings = MagicMock()
        settings.llm_max_retries = 3
        settings.llm_timeout_connect = 10.0
        settings.llm_timeout_read = 60.0
        settings.llm_backoff_base = 0.01
        settings.llm_backoff_max = 0.1
        mock_settings.return_value = settings

        # First two calls fail, third succeeds
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()
        success_response.json.return_value = {"message": {"content": "OK"}}

        mock_post.side_effect = [
            httpx.ConnectError("Connection refused"),
            httpx.ConnectError("Connection refused"),
            success_response,
        ]

        result = self._run(_call_ollama("model", [{"role": "user", "content": "hi"}], 0.5))
        self.assertEqual(result, "OK")
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("app.services.llm_service.get_settings")
    @patch("app.services.llm_service.asyncio.sleep", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    def test_raises_after_max_retries(self, mock_post, mock_sleep, mock_settings):
        settings = MagicMock()
        settings.llm_max_retries = 2
        settings.llm_timeout_connect = 10.0
        settings.llm_timeout_read = 60.0
        settings.llm_backoff_base = 0.01
        settings.llm_backoff_max = 0.1
        mock_settings.return_value = settings

        mock_post.side_effect = httpx.ReadTimeout("Timeout")

        with self.assertRaises(httpx.ReadTimeout):
            self._run(_call_ollama("model", [{"role": "user", "content": "hi"}], 0.5))

        self.assertEqual(mock_post.call_count, 2)

    @patch("app.services.llm_service.get_settings")
    @patch("httpx.AsyncClient.post")
    def test_http_4xx_not_retried(self, mock_post, mock_settings):
        settings = MagicMock()
        settings.llm_max_retries = 3
        settings.llm_timeout_connect = 10.0
        settings.llm_timeout_read = 60.0
        settings.llm_backoff_base = 0.01
        settings.llm_backoff_max = 0.1
        mock_settings.return_value = settings

        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        mock_post.side_effect = error

        with self.assertRaises(httpx.HTTPStatusError):
            self._run(_call_ollama("model", [{"role": "user", "content": "hi"}], 0.5))

        # 4xx should fail immediately, no retry
        self.assertEqual(mock_post.call_count, 1)

    @patch("app.services.llm_service.get_settings")
    @patch("app.services.llm_service.asyncio.sleep", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    def test_http_5xx_retried(self, mock_post, mock_sleep, mock_settings):
        settings = MagicMock()
        settings.llm_max_retries = 3
        settings.llm_timeout_connect = 10.0
        settings.llm_timeout_read = 60.0
        settings.llm_backoff_base = 0.01
        settings.llm_backoff_max = 0.1
        mock_settings.return_value = settings

        mock_500_response = MagicMock()
        mock_500_response.status_code = 500
        error_500 = httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_500_response)

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()
        success_response.json.return_value = {"message": {"content": "recovered"}}

        mock_post.side_effect = [error_500, success_response]

        result = self._run(_call_ollama("model", [{"role": "user", "content": "hi"}], 0.5))
        self.assertEqual(result, "recovered")
        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
