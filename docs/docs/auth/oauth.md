---
title: Google OAuth
sidebar_label: OAuth
sidebar_position: 1
---

# Google OAuth

The `sunholo.auth.oauth` module provides a Google OAuth2 flow with token caching and credential refresh.

## GoogleAuthManager

```python
from sunholo.auth.oauth import GoogleAuthManager

auth = GoogleAuthManager(
    client_id="your-client-id.apps.googleusercontent.com",
    client_secret="your-client-secret",
    scopes=["openid", "email", "profile"],
    redirect_uri="http://localhost:8000/callback",
)
```

### Get Authorization URL

```python
auth_url = auth.get_authorization_url(state="random-state-token")
# Redirect user to auth_url
```

### Exchange Code for Credentials

```python
# In your callback handler
credentials = await auth.exchange_code(code="auth-code-from-callback")
```

### Get or Refresh Credentials

```python
# Automatically handles token refresh
credentials = await auth.get_credentials(user_id="user@example.com")
```

### Token Caching

Tokens are cached in memory with automatic refresh on expiry. For persistent caching across restarts, you can provide a custom token store.
