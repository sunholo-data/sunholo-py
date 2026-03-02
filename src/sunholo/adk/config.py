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
ADK configuration and initialization.

Provides centralized ADK setup including:
- Database URL management (SQLite for demo, PostgreSQL for production)
- Session service creation with race condition protection (advisory locks)
- Artifact service initialization
- Memory and credential services

Usage:
    from sunholo.adk.config import ADKConfig

    config = ADKConfig(
        agents_dir="./agents",
        demo_mode=False,
        db_config={"host": "localhost", "port": 5432, ...},
    )
    session_service = config.create_session_service()
    artifact_service = config.create_artifact_service()
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from google.adk.sessions import DatabaseSessionService
    from google.adk.artifacts import BaseArtifactService

try:
    from google.adk.sessions import DatabaseSessionService
    from google.adk.memory import InMemoryMemoryService
    from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False

try:
    from sqlalchemy import text, create_engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ADKConfig:
    """Centralized ADK configuration and service factory.

    Manages creation of ADK services (session, artifact, memory, credential)
    with support for both demo (SQLite) and production (PostgreSQL) modes.

    The session service uses PostgreSQL advisory locks to prevent race conditions
    in multi-worker deployments.

    Args:
        agents_dir: Path to the directory containing agent definitions.
        demo_mode: If True, use SQLite instead of PostgreSQL.
        db_config: Database configuration dict with keys:
            user, password, host, port, database.
            Falls back to PGVECTOR_* environment variables.
        advisory_lock_id: PostgreSQL advisory lock ID for session table creation.
            Use a unique integer per deployment to prevent race conditions.
        app_name: Application name for branding and logging.
    """

    def __init__(
        self,
        agents_dir: str | Path = "./agents",
        demo_mode: bool | None = None,
        db_config: Dict[str, Any] | None = None,
        advisory_lock_id: int = 123456789,
        app_name: str = "sunholo",
    ):
        if not ADK_AVAILABLE:
            raise ImportError(
                "google-adk is required. Install with: pip install sunholo[adk]"
            )

        self.agents_dir = Path(agents_dir)
        self.app_name = app_name
        self.advisory_lock_id = advisory_lock_id

        # Determine demo mode
        if demo_mode is None:
            self.demo_mode = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes")
        else:
            self.demo_mode = demo_mode

        # Build database URL
        if self.demo_mode:
            self._db_url = "sqlite:///./demo_sessions.db"
        else:
            cfg = db_config or {}
            user = cfg.get("user", os.getenv("PGVECTOR_USER", "postgres"))
            password = cfg.get("password", os.getenv("PGVECTOR_PASSWORD", ""))
            host = cfg.get("host", os.getenv("PGVECTOR_HOST", "localhost"))
            port = cfg.get("port", os.getenv("PGVECTOR_PORT", "5432"))
            database = cfg.get("database", os.getenv("PGVECTOR_DATABASE", "postgres"))
            self._db_url = f"postgresql+pg8000://{user}:{password}@{host}:{port}/{database}"

        self._session_service: Optional[DatabaseSessionService] = None
        self._memory_service = None
        self._credential_service = None

    @property
    def db_url(self) -> str:
        """The database connection URL."""
        return self._db_url

    def _acquire_advisory_lock(self) -> None:
        """Acquire PostgreSQL advisory lock for safe DDL operations."""
        if self.demo_mode or not SQLALCHEMY_AVAILABLE:
            return
        try:
            engine = create_engine(self._db_url.replace("pg8000", "pg8000"))
            with engine.connect() as conn:
                conn.execute(text(f"SELECT pg_advisory_lock({self.advisory_lock_id})"))
                conn.commit()
            logger.info("Acquired advisory lock %d", self.advisory_lock_id)
        except Exception as e:
            logger.warning("Could not acquire advisory lock: %s", e)

    def _release_advisory_lock(self) -> None:
        """Release PostgreSQL advisory lock."""
        if self.demo_mode or not SQLALCHEMY_AVAILABLE:
            return
        try:
            engine = create_engine(self._db_url.replace("pg8000", "pg8000"))
            with engine.connect() as conn:
                conn.execute(text(f"SELECT pg_advisory_unlock({self.advisory_lock_id})"))
                conn.commit()
            logger.info("Released advisory lock %d", self.advisory_lock_id)
        except Exception as e:
            logger.warning("Could not release advisory lock: %s", e)

    def create_session_service(self) -> DatabaseSessionService:
        """Create or return cached ADK session service.

        Uses PostgreSQL advisory locks to prevent race conditions
        when multiple workers create the session table simultaneously.

        Returns:
            Configured DatabaseSessionService instance.
        """
        if self._session_service is not None:
            return self._session_service

        self._acquire_advisory_lock()
        try:
            self._session_service = DatabaseSessionService(db_url=self._db_url)
            logger.info("Created session service with DB: %s", "SQLite" if self.demo_mode else "PostgreSQL")
        finally:
            self._release_advisory_lock()

        return self._session_service

    def create_memory_service(self):
        """Create or return cached ADK memory service.

        Returns:
            InMemoryMemoryService instance.
        """
        if self._memory_service is None:
            self._memory_service = InMemoryMemoryService()
        return self._memory_service

    def create_credential_service(self):
        """Create or return cached ADK credential service.

        Returns:
            InMemoryCredentialService instance.
        """
        if self._credential_service is None:
            self._credential_service = InMemoryCredentialService()
        return self._credential_service
