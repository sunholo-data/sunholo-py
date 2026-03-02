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
HTTP-based artifact service for Google ADK.

Provides an abstract base and concrete implementations for persisting
ADK artifacts via HTTP APIs. This enables ADK agents to save/load
files and images without database coupling.

Architecture:
- Pure HTTP client (uses httpx)
- No database dependencies
- MIME-type based routing (images vs files)
- Token refresh on 401 Unauthorized
- Configurable endpoint paths

Usage:
    from sunholo.adk.artifacts import HttpArtifactService

    service = HttpArtifactService(
        base_url="https://api.example.com",
        auth_token="eyJ...",
        upload_path="/files/upload",
        download_path="/files/download/{file_id}",
        list_path="/files/list",
        delete_path="/files/delete",
    )

    # Use with ADK
    config = ADKConfig(...)
    runner = Runner(
        agent=agent,
        session_service=config.create_session_service(),
        artifact_service=service,
    )
"""
from __future__ import annotations

import base64
import logging
import mimetypes
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from google.adk.artifacts import BaseArtifactService
    from google.adk.artifacts.base_artifact_service import ArtifactVersion
    from google.genai import types

try:
    from google.adk.artifacts import BaseArtifactService
    from google.adk.artifacts.base_artifact_service import ArtifactVersion
    from google.genai import types
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

from sunholo.utils.http_client import post_with_retries

logger = logging.getLogger(__name__)


def _check_deps():
    if not ADK_AVAILABLE:
        raise ImportError(
            "google-adk is required. Install with: pip install sunholo[adk]"
        )
    if not HTTPX_AVAILABLE:
        raise ImportError(
            "httpx is required. Install with: pip install sunholo[adk]"
        )


class HttpArtifactService(BaseArtifactService if ADK_AVAILABLE else object):
    """HTTP-based artifact service for ADK agents.

    Stores and retrieves artifacts via HTTP APIs. Works with any backend
    that supports upload/download/list/delete operations.

    The service uses configurable URL path templates for each operation,
    with automatic token refresh on 401.

    Args:
        base_url: API base URL (e.g. "https://api.example.com").
        auth_token: Bearer token for authentication.
        upload_path: URL path for uploads. Receives multipart form data.
        download_path: URL path template for downloads.
            Use {file_id} placeholder for the file identifier.
        list_path: URL path for listing artifacts.
        delete_path: URL path for deleting artifacts.
        id_field: JSON field name for the file identifier in list responses.
        name_field: JSON field name for the filename in list responses.
        items_field: JSON field name for the items array in list responses.
        scope_field: JSON field name for the scope identifier (e.g. "assistant_id").
        scope_id: Scope identifier value.
        timeout: HTTP timeout in seconds.
        refresh_path: URL path for token refresh (optional).
    """

    def __init__(
        self,
        base_url: str,
        auth_token: str = "",
        upload_path: str = "/files/upload",
        download_path: str = "/files/download/{file_id}",
        list_path: str = "/files/list",
        delete_path: str = "/files/delete",
        id_field: str = "file_id",
        name_field: str = "file_name",
        items_field: str = "files",
        scope_field: str = "",
        scope_id: Any = None,
        timeout: float = 30.0,
        refresh_path: str = "",
    ):
        _check_deps()
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.upload_path = upload_path
        self.download_path = download_path
        self.list_path = list_path
        self.delete_path = delete_path
        self.id_field = id_field
        self.name_field = name_field
        self.items_field = items_field
        self.scope_field = scope_field
        self.scope_id = scope_id
        self.timeout = timeout
        self.refresh_path = refresh_path
        self.headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        self.client = httpx.AsyncClient(timeout=timeout)

    async def _refresh_token(self) -> Optional[str]:
        """Refresh the auth token via the refresh endpoint."""
        if not self.refresh_path:
            return None
        try:
            response = await self.client.post(
                f"{self.base_url}{self.refresh_path}",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                new_token = data.get("token")
                if new_token:
                    self.auth_token = new_token
                    self.headers = {"Authorization": f"Bearer {new_token}"}
                    logger.info("Token refreshed successfully")
                    return new_token
            return None
        except Exception as e:
            logger.error("Token refresh failed: %s", e)
            return None

    def _build_scope_payload(self, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Build JSON payload with scope field if configured."""
        payload: Dict[str, Any] = {}
        if self.scope_field and self.scope_id is not None:
            payload[self.scope_field] = self.scope_id
        if extra:
            payload.update(extra)
        return payload

    async def _find_file_id(self, filename: str, session_id: str | None = None) -> Optional[Any]:
        """Find file ID by filename in the listing."""
        payload = self._build_scope_payload()
        if session_id:
            payload["session_id"] = session_id

        response = await post_with_retries(
            self.client,
            f"{self.base_url}{self.list_path}",
            json=payload,
            headers=self.headers,
            on_401_refresh=self._refresh_token,
        )

        items = response.json().get(self.items_field, [])
        for item in items:
            if item.get(self.name_field) == filename:
                return item.get(self.id_field)
        return None

    async def save_artifact(
        self,
        *,
        filename: str,
        artifact: types.Part,
        app_name: str = "",
        user_id: str = "",
        session_id: Optional[str] = None,
        custom_metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """Upload artifact via HTTP.

        Implements delete-then-upload for replacements.

        Args:
            filename: Artifact filename.
            artifact: types.Part with inline_data.
            session_id: Optional session/thread scope.

        Returns:
            Version number (always 0, no versioning).
        """
        # Delete existing if present
        existing_id = await self._find_file_id(filename, session_id)
        if existing_id is not None:
            await self._delete_by_id(existing_id, session_id)

        # Upload
        files = {
            "files": (filename, artifact.inline_data.data, artifact.inline_data.mime_type)
        }
        data = self._build_scope_payload()
        if session_id:
            data["session_id"] = session_id

        await post_with_retries(
            self.client,
            f"{self.base_url}{self.upload_path}",
            data=data,
            files=files,
            headers=self.headers,
            timeout=60.0,
            on_401_refresh=self._refresh_token,
        )

        logger.info("Uploaded artifact: %s (MIME: %s)", filename, artifact.inline_data.mime_type)
        return 0

    async def load_artifact(
        self,
        *,
        filename: str,
        app_name: str = "",
        user_id: str = "",
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[types.Part]:
        """Download artifact by filename.

        Returns:
            types.Part with artifact data, or None if not found.
        """
        file_id = await self._find_file_id(filename, session_id)
        if file_id is None:
            return None

        download_url = f"{self.base_url}{self.download_path}".format(file_id=file_id)
        response = await self.client.get(download_url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        file_data = base64.b64decode(data.get("file_data", data.get("data", "")))

        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"

        logger.info("Loaded artifact: %s (MIME: %s, %d bytes)", filename, mime_type, len(file_data))
        return types.Part(
            inline_data=types.Blob(data=file_data, mime_type=mime_type)
        )

    async def list_artifact_keys(
        self,
        *,
        app_name: str = "",
        user_id: str = "",
        session_id: Optional[str] = None,
    ) -> list[str]:
        """List all artifact filenames.

        Returns:
            List of artifact filenames.
        """
        payload = self._build_scope_payload()
        if session_id:
            payload["session_id"] = session_id

        response = await post_with_retries(
            self.client,
            f"{self.base_url}{self.list_path}",
            json=payload,
            headers=self.headers,
            on_401_refresh=self._refresh_token,
        )

        items = response.json().get(self.items_field, [])
        return [item[self.name_field] for item in items if self.name_field in item]

    async def _delete_by_id(self, file_id: Any, session_id: str | None = None) -> None:
        """Delete an artifact by its ID."""
        payload = self._build_scope_payload({self.id_field: file_id})
        if session_id:
            payload["session_id"] = session_id

        await post_with_retries(
            self.client,
            f"{self.base_url}{self.delete_path}",
            json=payload,
            headers=self.headers,
            on_401_refresh=self._refresh_token,
        )

    async def delete_artifact(
        self,
        *,
        filename: str,
        app_name: str = "",
        user_id: str = "",
        session_id: Optional[str] = None,
    ) -> None:
        """Delete artifact by filename."""
        file_id = await self._find_file_id(filename, session_id)
        if file_id is not None:
            await self._delete_by_id(file_id, session_id)
            logger.info("Deleted artifact: %s", filename)

    async def list_versions(self, **kwargs) -> list[int]:
        """Always returns [0] (no versioning)."""
        return [0]

    async def list_artifact_versions(self, **kwargs) -> list[ArtifactVersion]:
        """Return single version if artifact exists."""
        artifact = await self.load_artifact(**kwargs)
        if not artifact:
            return []
        return [ArtifactVersion(
            canonical_uri=f"artifact://{kwargs.get('filename', 'unknown')}/v0",
            version=0,
            custom_metadata={},
        )]

    async def get_artifact_version(self, **kwargs) -> Optional[ArtifactVersion]:
        """Get version metadata."""
        versions = await self.list_artifact_versions(**kwargs)
        return versions[0] if versions else None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class MimeRoutingArtifactService(BaseArtifactService if ADK_AVAILABLE else object):
    """Artifact service that routes to different backends based on MIME type.

    Routes image artifacts to one service and other files to another.
    This is useful when images need thread-scoped storage while files
    are globally accessible.

    Args:
        image_service: Service for image artifacts (MIME starts with "image/").
        file_service: Service for non-image artifacts.
    """

    def __init__(
        self,
        image_service: HttpArtifactService,
        file_service: HttpArtifactService,
    ):
        _check_deps()
        self.image_service = image_service
        self.file_service = file_service

    def _is_image(self, mime_type: str) -> bool:
        return mime_type.startswith("image/")

    async def save_artifact(self, *, filename: str, artifact: types.Part, **kwargs) -> int:
        """Route save to image or file service based on MIME type."""
        mime_type = artifact.inline_data.mime_type
        # Handle string data (base64 encoded)
        data = artifact.inline_data.data
        if isinstance(data, str):
            try:
                artifact.inline_data.data = base64.b64decode(data)
            except Exception:
                artifact.inline_data.data = data.encode("utf-8")

        if self._is_image(mime_type):
            logger.info("Routing %s to image service (MIME: %s)", filename, mime_type)
            return await self.image_service.save_artifact(filename=filename, artifact=artifact, **kwargs)
        else:
            logger.info("Routing %s to file service (MIME: %s)", filename, mime_type)
            return await self.file_service.save_artifact(filename=filename, artifact=artifact, **kwargs)

    async def load_artifact(self, *, filename: str, **kwargs) -> Optional[types.Part]:
        """Try image service first, then file service."""
        result = await self.image_service.load_artifact(filename=filename, **kwargs)
        if result:
            return result
        return await self.file_service.load_artifact(filename=filename, **kwargs)

    async def list_artifact_keys(self, **kwargs) -> list[str]:
        """Combine keys from both services."""
        image_keys = await self.image_service.list_artifact_keys(**kwargs)
        file_keys = await self.file_service.list_artifact_keys(**kwargs)
        return image_keys + file_keys

    async def delete_artifact(self, *, filename: str, **kwargs) -> None:
        """Try to delete from both services."""
        try:
            await self.image_service.delete_artifact(filename=filename, **kwargs)
        except Exception:
            pass
        try:
            await self.file_service.delete_artifact(filename=filename, **kwargs)
        except Exception:
            pass

    async def list_versions(self, **kwargs) -> list[int]:
        return [0]

    async def list_artifact_versions(self, **kwargs) -> list[ArtifactVersion]:
        result = await self.load_artifact(**kwargs)
        if not result:
            return []
        return [ArtifactVersion(
            canonical_uri=f"artifact://{kwargs.get('filename', 'unknown')}/v0",
            version=0, custom_metadata={},
        )]

    async def get_artifact_version(self, **kwargs) -> Optional[ArtifactVersion]:
        versions = await self.list_artifact_versions(**kwargs)
        return versions[0] if versions else None

    async def close(self):
        """Close both service HTTP clients."""
        await self.image_service.close()
        await self.file_service.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
