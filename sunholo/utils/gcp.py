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
import os
import requests
import socket
# can't install due to circular import sunholo.logging
import logging


def is_running_on_cloudrun():
    """
    Check if the current environment is a Google Cloud Run instance.

    Returns:
        bool: `True` if running on Cloud Run, `False` otherwise.

    Example:
    ```python
    if is_running_on_cloudrun():
        print("Running on Cloud Run.")
    else:
        print("Not running on Cloud Run.")
    ```
    """
    if os.getenv("K_SERVICE"):
        return True
    return False



def is_gcp_logged_in():
    """
    Check if the current environment has valid Google Cloud Platform (GCP) credentials.

    This function attempts to obtain the default application credentials from the environment.
    It will return `True` if credentials are available, otherwise it returns `False`.

    Returns:
        bool: `True` if GCP credentials are available, `False` otherwise.

    Example:
    ```python
    if is_gcp_logged_in():
        print("GCP credentials found.")
    else:
        print("GCP credentials not found or invalid.")
    ```
    """
    try:
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError
        credentials, project = google.auth.default()
        return True
    except DefaultCredentialsError:
        return False

is_gcp_cached = None  # Global variable for caching the result
def is_running_on_gcp():
    """
    Check if the current environment is a Google Cloud Platform (GCP) instance.

    This function attempts to reach the GCP metadata server to determine if the code
    is running on a GCP instance.

    Returns:
        bool: `True` if running on GCP, `False` otherwise.

    Example:
    ```python
    if is_running_on_gcp():
        print("Running on GCP.")
    else:
        print("Not running on GCP.")
    ```
    """
    global is_gcp_cached
    if is_gcp_cached is not None:
        return is_gcp_cached

    try:
        # Google Cloud instances can reach the metadata server
        socket.setdefaulttimeout(1)
        socket.socket().connect(('metadata.google.internal', 80))
        is_gcp_cached = True
    except (socket.timeout, socket.error):
        is_gcp_cached = False

    return is_gcp_cached

def get_service_account_email():
    """
    Retrieve the service account email from environment variables or the GCP metadata server.

    Returns:
        str or None: The service account email if found, None otherwise.
    """
    service_email = os.getenv("GCP_DEFAULT_SERVICE_EMAIL")
    if service_email:
        return service_email
    service_email = get_metadata('instance/service-accounts/default/email')
    os.environ['GCP_DEFAULT_SERVICE_EMAIL'] = service_email
    return service_email



def get_region():
    """
    Retrieve the region of the GCP instance.

    This function attempts to retrieve the region by extracting it from the zone information
    available in the GCP metadata server.

    Returns:
        str or None: The region if found, None otherwise.
    """
    if not is_running_on_gcp():
        return None
    # The "instance/zone" metadata includes the region as part of the zone name
    region = os.getenv("GCP_REGION")
    if region:
        return region
    
    zone = get_metadata('instance/zone')
    if zone:
        # Split by '/' and take the last part, then split by '-' and take all but the last part
        region_zone = zone.split('/')[-1]
        region = '-'.join(region_zone.split('-')[:-1])
        os.environ["GCP_REGION"] = region
        return region
    return None

def get_metadata(stem):
    """
    Retrieve metadata information from the GCP metadata server.

    Args:
        stem (str): The metadata path to query.

    Returns:
        str or None: The metadata information if found, None otherwise.
    """
    if not is_running_on_gcp():
        return None
    
    metadata_server_url = f'http://metadata.google.internal/computeMetadata/v1/{stem}'

    headers = {'Metadata-Flavor': 'Google'}

    response = requests.get(metadata_server_url, headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        print(f"Request failed with status code {response.status_code}")
        return None
