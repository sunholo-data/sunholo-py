#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Async HTTP client utilities with exponential backoff, jitter, and token refresh.

Provides robust HTTP GET and POST operations with:
- Exponential backoff with configurable jitter
- Automatic retry on transient failures (429, 500-504)
- Token refresh callback on 401 Unauthorized
- Chunked streaming for large responses

Usage:
    from sunholo.utils.http_client import get_with_retries, post_with_retries

    # Simple GET with retry
    body, content_type = await get_with_retries("https://api.example.com/data")

    # POST with token refresh
    async with httpx.AsyncClient() as client:
        resp = await post_with_retries(
            client, "https://api.example.com/submit",
            json={"key": "value"},
            on_401_refresh=my_token_refresh_fn,
        )
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Callable, Iterable, Optional, Set, Tuple

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_RETRY_STATUSES: Set[int] = {429, 500, 501, 502, 503, 504}

# Type alias for token refresh callbacks
TokenRefreshCallback = Callable[[], Any]


def _check_httpx():
    if not HTTPX_AVAILABLE:
        raise ImportError(
            "httpx is required for HTTP client utilities. "
            "Install with: pip install sunholo[adk] or pip install httpx"
        )


async def _should_retry_response(resp, retry_statuses: Iterable[int]) -> bool:
    """Check if a response status code is retryable."""
    return resp.status_code in retry_statuses


async def get_with_retries(
    url: str,
    *,
    headers: dict | None = None,
    timeout: float = 120.0,
    max_attempts: int = 5,
    base_backoff: float = 0.5,
    max_backoff: float = 10.0,
    jitter: float = 0.25,
    retry_statuses: Set[int] | None = None,
    follow_redirects: bool = True,
) -> Tuple[bytes, str]:
    """GET with exponential backoff + jitter and retry on transient errors.

    Args:
        url: The URL to fetch.
        headers: Optional HTTP headers.
        timeout: Request timeout in seconds.
        max_attempts: Total attempts including the first.
        base_backoff: Initial delay in seconds before first retry.
        max_backoff: Maximum delay in seconds between retries.
        jitter: Fraction of random jitter applied to backoff (0-1).
        retry_statuses: HTTP status codes to retry on. Defaults to {429, 500-504}.
        follow_redirects: Whether to follow HTTP redirects.

    Returns:
        Tuple of (response_bytes, content_type).

    Raises:
        httpx.HTTPStatusError: If all attempts fail with a retryable status.
        httpx.RequestError: If all attempts fail with a transport error.
    """
    _check_httpx()
    if retry_statuses is None:
        retry_statuses = DEFAULT_RETRY_STATUSES

    attempt = 0
    last_exc: Exception | None = None
    http_timeout = httpx.Timeout(timeout, connect=10.0, read=timeout, write=timeout)

    async with httpx.AsyncClient(timeout=http_timeout) as client:
        while attempt < max_attempts:
            attempt += 1
            try:
                resp = await client.get(url, headers=headers, follow_redirects=follow_redirects)

                if await _should_retry_response(resp, retry_statuses):
                    logger.warning(
                        "Retryable response %s from %s (attempt %d/%d)",
                        resp.status_code, url, attempt, max_attempts
                    )
                    last_exc = httpx.HTTPStatusError(
                        "retryable status", request=resp.request, response=resp
                    )
                    await resp.aclose()
                else:
                    resp.raise_for_status()
                    content_type = resp.headers.get("content-type", "") or ""
                    chunks = []
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        if chunk:
                            chunks.append(chunk)
                    await resp.aclose()
                    return (b"".join(chunks), content_type)

            except (
                httpx.RequestError, httpx.RemoteProtocolError,
                httpx.ReadTimeout, httpx.WriteTimeout, httpx.ConnectTimeout
            ) as e:
                last_exc = e
                logger.warning(
                    "HTTP error for %s (attempt %d/%d): %s",
                    url, attempt, max_attempts, e
                )

            if attempt >= max_attempts:
                break

            backoff = min(base_backoff * (2 ** (attempt - 1)), max_backoff)
            jitter_amt = random.uniform(-jitter * backoff, jitter * backoff)
            sleep_for = max(0.0, backoff + jitter_amt)
            logger.debug(
                "Sleeping %.2fs before retrying %s (attempt %d/%d)",
                sleep_for, url, attempt + 1, max_attempts
            )
            await asyncio.sleep(sleep_for)

    if isinstance(last_exc, httpx.HTTPStatusError):
        raise last_exc
    if last_exc:
        raise last_exc
    raise RuntimeError("get_with_retries: failed without exception")


async def post_with_retries(
    client,
    url: str,
    *,
    data: Any = None,
    json: Any = None,
    files: Any = None,
    headers: dict | None = None,
    timeout: float | None = 30.0,
    max_attempts: int = 5,
    base_backoff: float = 0.5,
    max_backoff: float = 10.0,
    jitter: float = 0.25,
    retry_statuses: Set[int] | None = None,
    raise_for_status: bool = True,
    on_401_refresh: Optional[TokenRefreshCallback] = None,
):
    """POST with exponential backoff + jitter, retry, and optional 401 token refresh.

    Args:
        client: An httpx.AsyncClient instance.
        url: The URL to POST to.
        data: Form data to send.
        json: JSON data to send.
        files: Files to upload.
        headers: Optional HTTP headers.
        timeout: Request timeout in seconds.
        max_attempts: Total attempts including the first.
        base_backoff: Initial delay in seconds before first retry.
        max_backoff: Maximum delay in seconds between retries.
        jitter: Fraction of random jitter applied to backoff (0-1).
        retry_statuses: HTTP status codes to retry on. Defaults to {429, 500-504}.
        raise_for_status: Whether to raise on non-2xx responses.
        on_401_refresh: Async or sync callback returning a new auth token on 401.
            If provided and the server returns 401, this callback is invoked once
            to refresh the token, and the request is retried with the new token.

    Returns:
        httpx.Response object.

    Raises:
        httpx.HTTPStatusError: If all attempts fail with a retryable status.
        httpx.RequestError: If all attempts fail with a transport error.
    """
    _check_httpx()
    if retry_statuses is None:
        retry_statuses = DEFAULT_RETRY_STATUSES

    attempt = 0
    last_exc: Exception | None = None
    token_refreshed = False

    while attempt < max_attempts:
        attempt += 1
        try:
            resp = await client.post(
                url, data=data, json=json, files=files,
                headers=headers, timeout=timeout
            )

            # Handle 401 with token refresh
            if resp.status_code == 401 and on_401_refresh and not token_refreshed:
                logger.warning("401 Unauthorized from %s - attempting token refresh", url)
                try:
                    if asyncio.iscoroutinefunction(on_401_refresh):
                        new_token = await on_401_refresh()
                    else:
                        new_token = on_401_refresh()

                    if new_token:
                        if headers is None:
                            headers = {}
                        headers["Authorization"] = f"Bearer {new_token}"
                        token_refreshed = True
                        logger.info("Token refreshed, retrying request to %s", url)
                        continue
                    else:
                        logger.warning("Token refresh returned None")
                except Exception as refresh_err:
                    logger.error("Token refresh failed: %s", refresh_err)

            if await _should_retry_response(resp, retry_statuses):
                logger.warning(
                    "Retryable response %s from %s (attempt %d/%d)",
                    resp.status_code, url, attempt, max_attempts
                )
                last_exc = httpx.HTTPStatusError(
                    "retryable status", request=resp.request, response=resp
                )
            else:
                if raise_for_status:
                    resp.raise_for_status()
                return resp

        except (
            httpx.RequestError, httpx.RemoteProtocolError,
            httpx.ReadTimeout, httpx.WriteTimeout, httpx.ConnectTimeout
        ) as e:
            last_exc = e
            logger.warning(
                "HTTP error for %s (attempt %d/%d): %s",
                url, attempt, max_attempts, e
            )

        if attempt >= max_attempts:
            break

        backoff = min(base_backoff * (2 ** (attempt - 1)), max_backoff)
        jitter_amt = random.uniform(-jitter * backoff, jitter * backoff)
        sleep_for = max(0.0, backoff + jitter_amt)
        logger.debug(
            "Sleeping %.2fs before retrying %s (attempt %d/%d)",
            sleep_for, url, attempt + 1, max_attempts
        )
        await asyncio.sleep(sleep_for)

    if isinstance(last_exc, httpx.HTTPStatusError):
        raise last_exc
    if last_exc:
        raise last_exc
    raise RuntimeError("post_with_retries: failed without exception")
