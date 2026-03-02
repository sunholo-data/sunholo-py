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
Robust Firestore client with retry, circuit breaker, and async/sync fallback.

Provides a production-hardened Firestore client that handles:
- Event loop closed errors with automatic async/sync fallback
- Retry logic with exponential backoff for transient failures
- Context-aware timeouts for different use cases
- Circuit breaker pattern to prevent cascading failures

Usage:
    from sunholo.database.firestore import get_firestore_client

    client = get_firestore_client("email")
    doc_id = await client.add_document("my_collection", {"key": "value"})
    doc = await client.get_document("my_collection/doc_id")
    results = await client.query_collection("my_collection", "field", "==", "value")
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from google.cloud import firestore as firestore_types

try:
    from google.cloud import firestore
    from google.api_core import exceptions as google_exceptions
    FIRESTORE_AVAILABLE = True
except ImportError:
    firestore = None
    google_exceptions = None
    FIRESTORE_AVAILABLE = False

try:
    from tenacity import (
        retry, stop_after_attempt, wait_exponential,
        retry_if_exception_type, before_sleep_log,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

from sunholo.utils.timeout_config import TimeoutConfig

logger = logging.getLogger(__name__)


def _check_deps():
    if not FIRESTORE_AVAILABLE:
        raise ImportError(
            "google-cloud-firestore is required. "
            "Install with: pip install sunholo[firestore]"
        )


# Retryable Firestore exceptions
def _get_retryable_exceptions():
    if not FIRESTORE_AVAILABLE:
        return (ConnectionError, OSError, RuntimeError)
    return (
        google_exceptions.DeadlineExceeded,
        google_exceptions.ServiceUnavailable,
        google_exceptions.InternalServerError,
        google_exceptions.ResourceExhausted,
        google_exceptions.Aborted,
        ConnectionError,
        OSError,
        RuntimeError,
    )


class FirestoreClient:
    """Context-aware Firestore client with robust error handling.

    Automatically falls back from async to sync operations when
    event loop issues are detected (common in multi-worker deployments).

    Args:
        context: Operational context ("ui", "email", "whatsapp", etc.)
            Controls retry aggressiveness and timeouts.
    """

    def __init__(self, context: str = "ui"):
        _check_deps()
        self.context = context
        self.timeouts = TimeoutConfig.get_timeouts(context)
        self._async_client = None
        self._sync_client = None

    @property
    def async_client(self):
        """Get async Firestore client, creating if needed."""
        if self._async_client is None:
            self._async_client = firestore.AsyncClient()
        return self._async_client

    @property
    def sync_client(self):
        """Get sync Firestore client, creating if needed."""
        if self._sync_client is None:
            self._sync_client = firestore.Client()
        return self._sync_client

    def create_retry_decorator(self):
        """Create a context-aware retry decorator.

        Email/background contexts get more aggressive retries.
        """
        if not TENACITY_AVAILABLE:
            # No-op decorator if tenacity not available
            def noop(func):
                return func
            return noop

        retry_config = TimeoutConfig.get_retry_config(self.context)
        return retry(
            stop=stop_after_attempt(retry_config["stop_attempts"]),
            wait=wait_exponential(
                multiplier=retry_config["wait_multiplier"],
                min=retry_config["wait_min"],
                max=retry_config["wait_max"],
            ),
            retry=retry_if_exception_type(_get_retryable_exceptions()),
            before_sleep=before_sleep_log(logger, logging.INFO),
            reraise=True,
        )

    async def _with_sync_fallback(self, async_op, sync_op):
        """Execute async operation with automatic sync fallback on event loop issues."""
        try:
            return await async_op()
        except RuntimeError as e:
            if "Event loop is closed" in str(e) or "no running event loop" in str(e).lower():
                logger.warning("Event loop issue, falling back to sync: %s", e)
                return sync_op()
            raise

    async def add_document(self, collection_path: str, data: Dict[str, Any]) -> Optional[str]:
        """Add a document with retry and async/sync fallback.

        Args:
            collection_path: Firestore collection path.
            data: Document data.

        Returns:
            Document ID if successful, None otherwise.
        """
        retry_dec = self.create_retry_decorator()

        @retry_dec
        async def _add():
            async def _async():
                ref = self.async_client.collection(collection_path)
                _, doc_ref = await ref.add(data)
                return doc_ref.id

            def _sync():
                ref = self.sync_client.collection(collection_path)
                _, doc_ref = ref.add(data)
                return doc_ref.id

            return await self._with_sync_fallback(_async, _sync)

        try:
            doc_id = await _add()
            logger.info("Added document to %s: %s", collection_path, doc_id)
            return doc_id
        except Exception as e:
            logger.error("Failed to add document to %s: %s", collection_path, e)
            return None

    async def set_document(self, document_path: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """Set a document with retry and async/sync fallback.

        Args:
            document_path: Full document path (collection/doc_id).
            data: Document data.
            merge: If True, merge with existing data.

        Returns:
            True if successful.
        """
        retry_dec = self.create_retry_decorator()

        @retry_dec
        async def _set():
            async def _async():
                ref = self.async_client.document(document_path)
                await ref.set(data, merge=merge)
                return True

            def _sync():
                ref = self.sync_client.document(document_path)
                ref.set(data, merge=merge)
                return True

            return await self._with_sync_fallback(_async, _sync)

        try:
            return await _set()
        except Exception as e:
            logger.error("Failed to set document at %s: %s", document_path, e)
            return False

    async def get_document(self, document_path: str) -> Optional[Dict[str, Any]]:
        """Get a document with retry and async/sync fallback.

        Args:
            document_path: Full document path (collection/doc_id).

        Returns:
            Document data dict, or None if not found.
        """
        retry_dec = self.create_retry_decorator()

        @retry_dec
        async def _get():
            async def _async():
                ref = self.async_client.document(document_path)
                doc = await ref.get()
                return doc.to_dict() if doc.exists else None

            def _sync():
                ref = self.sync_client.document(document_path)
                doc = ref.get()
                return doc.to_dict() if doc.exists else None

            return await self._with_sync_fallback(_async, _sync)

        try:
            return await _get()
        except Exception as e:
            logger.error("Failed to get document %s: %s", document_path, e)
            return None

    async def query_collection(
        self,
        collection_path: str,
        field: str,
        operator: str,
        value: Any,
        limit: int | None = None,
        include_ids: bool = False,
    ) -> Union[List[Dict[str, Any]], List[tuple]]:
        """Query a collection with retry and async/sync fallback.

        Args:
            collection_path: Firestore collection path.
            field: Field to filter on.
            operator: Comparison operator ("==", ">=", "in", etc.).
            value: Value to compare against.
            limit: Maximum results to return.
            include_ids: If True, return list of (doc_id, data) tuples.

        Returns:
            List of document dicts, or list of (id, dict) tuples.
        """
        retry_dec = self.create_retry_decorator()

        @retry_dec
        async def _query():
            async def _async():
                ref = self.async_client.collection(collection_path)
                query = ref.where(field, operator, value)
                if limit:
                    query = query.limit(limit)
                docs = await query.get()
                if include_ids:
                    return [(doc.id, doc.to_dict()) for doc in docs]
                return [doc.to_dict() for doc in docs]

            def _sync():
                ref = self.sync_client.collection(collection_path)
                query = ref.where(field, operator, value)
                if limit:
                    query = query.limit(limit)
                docs = query.get()
                if include_ids:
                    return [(doc.id, doc.to_dict()) for doc in docs]
                return [doc.to_dict() for doc in docs]

            return await self._with_sync_fallback(_async, _sync)

        try:
            return await _query()
        except Exception as e:
            logger.error("Failed to query %s: %s", collection_path, e)
            return []


class FirestoreCircuitBreaker:
    """Circuit breaker for Firestore operations to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through.
    - OPEN: Failure threshold exceeded, requests are blocked.
    - HALF_OPEN: Recovery timeout elapsed, single test request allowed.

    Args:
        failure_threshold: Number of failures before opening the circuit.
        recovery_timeout: Seconds to wait before trying again after opening.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"

    async def call(self, operation):
        """Execute an operation with circuit breaker protection.

        Args:
            operation: Async callable to execute.

        Returns:
            Result of the operation.

        Raises:
            Exception: If the circuit is open or the operation fails.
        """
        if self.state == "OPEN":
            if (self.last_failure_time and
                    time.time() - self.last_failure_time > self.recovery_timeout):
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception(f"Circuit breaker OPEN (failures: {self.failure_count})")

        try:
            result = await operation()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("Circuit breaker OPEN after %d failures", self.failure_count)
            raise


# Global client and circuit breaker caches
_firestore_clients: Dict[str, FirestoreClient] = {}
_circuit_breakers: Dict[str, FirestoreCircuitBreaker] = {}


def get_firestore_client(context: str = "ui") -> FirestoreClient:
    """Get a cached, context-appropriate Firestore client.

    Args:
        context: Operational context ("ui", "email", "whatsapp", etc.).

    Returns:
        Configured FirestoreClient instance.
    """
    if context not in _firestore_clients:
        _firestore_clients[context] = FirestoreClient(context)
    return _firestore_clients[context]


def get_circuit_breaker(context: str = "ui") -> FirestoreCircuitBreaker:
    """Get a cached circuit breaker for the given context.

    Args:
        context: Operational context.

    Returns:
        Configured FirestoreCircuitBreaker instance.
    """
    if context not in _circuit_breakers:
        if context in ("email", "whatsapp"):
            _circuit_breakers[context] = FirestoreCircuitBreaker(
                failure_threshold=3, recovery_timeout=30
            )
        else:
            _circuit_breakers[context] = FirestoreCircuitBreaker(
                failure_threshold=5, recovery_timeout=60
            )
    return _circuit_breakers[context]
