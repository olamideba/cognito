import unittest
from unittest.mock import AsyncMock, patch
from core.utils import retry_with_backoff

class RetryBackoffTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_success_first_attempt(self) -> None:
        mock_func = AsyncMock(return_value="success")
        decorated = retry_with_backoff(retries=3)(mock_func)
        
        result = await decorated()
        self.assertEqual(result, "success")
        mock_func.assert_awaited_once()

    async def test_retry_success_after_failure(self) -> None:
        mock_func = AsyncMock()
        mock_func.side_effect = [ValueError("failed"), "success"]
        decorated = retry_with_backoff(retries=3, exceptions=(ValueError,))(mock_func)
        
        with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
            result = await decorated()
            self.assertEqual(result, "success")
            self.assertEqual(mock_func.call_count, 2)
            mock_sleep.assert_awaited_once()

    async def test_retry_fails_after_max_retries(self) -> None:
        mock_func = AsyncMock()
        mock_func.side_effect = ValueError("permanent error")
        decorated = retry_with_backoff(retries=3, exceptions=(ValueError,))(mock_func)
        
        with (
            patch("asyncio.sleep", AsyncMock()) as mock_sleep,
            self.assertRaises(ValueError)
        ):
            await decorated()
        
        self.assertEqual(mock_func.call_count, 4)  # 1 initial + 3 retries
        self.assertEqual(mock_sleep.call_count, 3)

    async def test_retry_non_matching_exception_raises_immediately(self) -> None:
        mock_func = AsyncMock()
        mock_func.side_effect = TypeError("wrong error")
        decorated = retry_with_backoff(retries=3, exceptions=(ValueError,))(mock_func)
        
        with self.assertRaises(TypeError):
            await decorated()
            
        mock_func.assert_awaited_once()
