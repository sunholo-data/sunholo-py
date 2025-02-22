from sunholo.discovery_engine import DiscoveryEngineClient 

# Replace with your actual project ID and location
PROJECT_ID = "multivac-internal-dev"
LOCATION = "eu"

print(f"{PROJECT_ID=} {LOCATION=}")

# Data store IDs to test
# They should be of the format projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id} if collection is not default
DATA_STORE_IDS = [
    "aitana", #default collection
    "projects/multivac-internal-dev/locations/eu/collections/default_collection/dataStores/sunholo-drive-datastore",
    "projects/multivac-internal-dev/locations/eu/collections/sunholo-gmail-datastore/dataStores/sunholo-gmail-datastore_google_mail",
    # Add other data store IDs as needed
]

def test_discovery_engine_client(project_id, location, data_store_ids):
    """
    Tests the functionality of your DiscoveryEngineClient class with multiple and single data stores.
    """

    def test_search(client, query, data_store_ids=None):
        """
        Performs a search and prints the results.
        """
        try:
            search_response = client.get_chunks(
                query=query,
                data_store_ids=data_store_ids
            )

            print("Search results:")
            if isinstance(search_response, str):
                print(search_response)
            else:
                for result in search_response.results:
                    print(f"  - Document: {result.document.name}")

        except Exception as e:
            print(f"Error during search: {e}")

    # 1. Test with multiple data stores
    client = DiscoveryEngineClient(data_store_id="aitana", project_id=PROJECT_ID, location=LOCATION)
    test_query = "who is Mark Edmondson?"
    print(f"Testing search with multiple data stores: {data_store_ids}")
    test_search(client, test_query, data_store_ids)

    data_store_ids = [
        "aitana", #default collection
        "sunholo-drive-datastore",
        "sunholo-gmail-datastore_google_mail",
        # Add other data store IDs as needed
    ]
    # 2. Test with a single data store
    for data_store_id in data_store_ids:
        client = DiscoveryEngineClient(data_store_id, project_id=PROJECT_ID, location=LOCATION)
        client.data_store_id = data_store_id  # Set data store ID for the client
        test_query = "What is Pexpark?"
        print(f"\nTesting search with single data store: {data_store_id}")
        test_search(client, test_query)

# Run the tests
test_discovery_engine_client(PROJECT_ID, LOCATION, DATA_STORE_IDS)