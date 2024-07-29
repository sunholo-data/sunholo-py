import os
try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
except ImportError:
    DefaultAzureCredential = None
    ClientSecretCredential = None

from ..custom_logging import log

def azure_auth():
    """
    Will attempt to authenticate using default credentials first (e.g. you are running within Azure Container Apps or similar)

    If default credentials are not available, will attempt to authenticate via env vars - set up via:

    ```bash
    az ad sp create-for-rbac --name "myApp" --role contributor \
        --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
        --sdk-auth

    export AZURE_CLIENT_ID="your-client-id"
    export AZURE_CLIENT_SECRET="your-client-secret"
    export AZURE_TENANT_ID="your-tenant-id"
    ```

    """
    if DefaultAzureCredential is None: 
        raise ImportError("Azure identity credentials library needed - install via `pip install sunholo[azure]`")
    
    # Use DefaultAzureCredential to authenticate
    try:
        credential = DefaultAzureCredential()
        return credential
    
    except Exception as e:
        log.error(f"Failed to authenticate with default credentials: {str(e)}")
        log.info("Attempting to authenticate using ClientSecretCredential")

        # Use ClientSecretCredential to authenticate with a service principal
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")

        if not client_id or not client_secret or not tenant_id:
            log.error("Service principal credentials are not set in environment variables")
            return None

        if ClientSecretCredential is None:
            raise ImportError("Azure identity credentials library needed - install via `pip install sunholo[azure]`")

        try:
            credential = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id
            )
            return credential
        except Exception as e:
            log.error(f"Failed to authenticate with service principal: {str(e)}")
            return None
        
