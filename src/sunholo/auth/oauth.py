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
Google OAuth2 authentication manager.

Provides a unified authentication flow with support for:
- Saved tokens (from previous interactive auth)
- Application Default Credentials (ADC)
- gcloud CLI credentials
- Interactive OAuth2 browser flow

Usage:
    from sunholo.auth.oauth import GoogleAuthManager

    auth = GoogleAuthManager(config_dir="~/.sunholo")
    creds = auth.get_credentials()
    email = auth.get_user_email()

    # Or interactive login
    auth.authenticate_interactive(client_secrets_file="credentials.json")
"""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

try:
    from google.auth import default
    from google.auth.transport.requests import Request
    from google.auth.exceptions import DefaultCredentialsError
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    OAUTHLIB_AVAILABLE = True
except ImportError:
    OAUTHLIB_AVAILABLE = False

logger = logging.getLogger(__name__)


class GoogleAuthManager:
    """Manages Google OAuth2 authentication with multiple credential sources.

    Credential resolution order:
    1. Explicit override (passed as parameter)
    2. Cached credentials (in-memory)
    3. Saved token file
    4. Application Default Credentials
    5. gcloud CLI config

    Args:
        config_dir: Directory for storing auth tokens.
            Defaults to ~/.sunholo.
        scopes: OAuth2 scopes to request.
    """

    DEFAULT_SCOPES = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    def __init__(
        self,
        config_dir: str | Path | None = None,
        scopes: List[str] | None = None,
    ):
        if not GOOGLE_AUTH_AVAILABLE:
            raise ImportError(
                "google-auth is required. "
                "Install with: pip install google-auth google-auth-oauthlib"
            )

        self.config_dir = Path(config_dir or Path.home() / ".sunholo")
        self.config_dir.mkdir(exist_ok=True)
        self.scopes = scopes or self.DEFAULT_SCOPES

        self.token_file = self.config_dir / "google_token.json"
        self.credentials_file = self.config_dir / "credentials.json"
        self.user_config_file = self.config_dir / "user_config.json"

        self._cached_email: Optional[str] = None
        self._cached_creds: Optional[Credentials] = None

    def save_user_email(self, email: str) -> None:
        """Save user email preference to config.

        Args:
            email: Email address to save.
        """
        try:
            config = {}
            if self.user_config_file.exists():
                with open(self.user_config_file, "r") as f:
                    config = json.load(f)

            config["user_email"] = email
            config["updated_at"] = datetime.now().isoformat()

            with open(self.user_config_file, "w") as f:
                json.dump(config, f, indent=2)

            self.user_config_file.chmod(0o600)
            self._cached_email = email
            logger.info("Saved user email: %s", email)
        except Exception as e:
            logger.error("Could not save user email: %s", e)

    def get_saved_user_email(self) -> Optional[str]:
        """Get saved user email from config file."""
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, "r") as f:
                    config = json.load(f)
                    return config.get("user_email")
            except Exception as e:
                logger.debug("Could not load user config: %s", e)
        return None

    def get_user_email(self, override_email: Optional[str] = None) -> Optional[str]:
        """Get the authenticated user's email address.

        Resolution order: override > cached > saved > gcloud > credentials.

        Args:
            override_email: Explicit email override.

        Returns:
            User email or None.
        """
        if override_email:
            return override_email
        if self._cached_email:
            return self._cached_email

        saved = self.get_saved_user_email()
        if saved:
            self._cached_email = saved
            return saved

        gcloud_email = self._get_gcloud_email()
        if gcloud_email:
            self._cached_email = gcloud_email
            return gcloud_email

        creds = self.get_credentials()
        if creds and hasattr(creds, "service_account_email"):
            self._cached_email = creds.service_account_email
            return self._cached_email

        return None

    def get_credentials(self) -> Optional[Credentials]:
        """Get valid Google credentials.

        Tries saved token, then ADC, with automatic refresh.

        Returns:
            Google Credentials object or None.
        """
        if self._cached_creds and self._cached_creds.valid:
            return self._cached_creds

        creds = None

        # Try saved token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_file), self.scopes
                )
            except Exception as e:
                logger.debug("Could not load saved token: %s", e)

        # Try Application Default Credentials
        if not creds or not creds.valid:
            try:
                creds, project = default(scopes=self.scopes)
                logger.info("Using ADC (project: %s)", project)
            except DefaultCredentialsError:
                logger.debug("No Application Default Credentials found")

        # Refresh if needed
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self._save_credentials(creds)
                except Exception as e:
                    logger.debug("Could not refresh token: %s", e)
                    creds = None

        self._cached_creds = creds
        return creds

    def authenticate_interactive(self, client_secrets_file: str = "") -> bool:
        """Perform interactive OAuth2 authentication via browser.

        Args:
            client_secrets_file: Path to OAuth2 client secrets JSON.
                Defaults to {config_dir}/credentials.json.

        Returns:
            True if authentication successful.
        """
        if not OAUTHLIB_AVAILABLE:
            raise ImportError(
                "google-auth-oauthlib is required for interactive auth. "
                "Install with: pip install google-auth-oauthlib"
            )

        client_file = client_secrets_file or str(self.credentials_file)
        if not Path(client_file).exists():
            logger.error(
                "No OAuth2 client secrets file at %s. "
                "Download from Google Cloud Console.", client_file
            )
            return False

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_file, self.scopes
            )
            creds = flow.run_local_server(
                port=0,
                success_message="Authentication successful! You can close this window.",
                open_browser=True,
            )
            self._save_credentials(creds)
            self._cached_creds = creds
            self._cached_email = None
            logger.info("Authentication successful!")
            return True
        except Exception as e:
            logger.error("Authentication failed: %s", e)
            return False

    def _save_credentials(self, creds: Credentials) -> None:
        """Save credentials to token file with restrictive permissions."""
        try:
            token_data = {
                "type": "authorized_user",
                "client_id": getattr(creds, "client_id", ""),
                "client_secret": getattr(creds, "client_secret", ""),
                "refresh_token": getattr(creds, "refresh_token", ""),
            }
            with open(self.token_file, "w") as f:
                json.dump(token_data, f)
            self.token_file.chmod(0o600)
        except Exception as e:
            logger.debug("Could not save credentials: %s", e)

    def _get_gcloud_email(self) -> Optional[str]:
        """Try to get email from gcloud CLI config."""
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "account"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                email = result.stdout.strip()
                if email and "@" in email:
                    return email
        except Exception as e:
            logger.debug("Could not get gcloud email: %s", e)
        return None

    def logout(self) -> None:
        """Clear stored credentials and cached state."""
        if self.token_file.exists():
            self.token_file.unlink()
        self._cached_creds = None
        self._cached_email = None
        logger.info("Logged out successfully")

    def status(self) -> Dict[str, Any]:
        """Get authentication status summary.

        Returns:
            Dict with authenticated, email, token_file, using_adc, scopes.
        """
        creds = self.get_credentials()
        email = self.get_user_email()
        return {
            "authenticated": bool(creds and creds.valid),
            "email": email,
            "token_file": str(self.token_file) if self.token_file.exists() else None,
            "using_adc": bool(creds and not self.token_file.exists()),
            "scopes": list(creds.scopes) if creds and hasattr(creds, "scopes") and creds.scopes else [],
        }
