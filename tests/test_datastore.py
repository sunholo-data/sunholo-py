from sunholo.discovery_engine import DiscoveryEngineClient 

# Replace with your actual project ID and location
PROJECT_ID = "multivac-internal-dev"
LOCATION = "eu"

print(f"{PROJECT_ID=} {LOCATION=}")

# Data store IDs to test
# They should be of the format projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id} if collection is not default
DATA_STORE_IDS = [
    "aitana", #default collection
    #"projects/multivac-internal-dev/locations/eu/collections/default_collection/dataStores/sunholo-drive-datastore",
    #"projects/multivac-internal-dev/locations/eu/collections/sunholo-gmail-datastore/dataStores/sunholo-gmail-datastore_google_mail",
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
            if not search_response:
                return f"No results found for {client.data_store_id=} {data_store_ids=}"
            if isinstance(search_response, str):
                print(f"Found search_response for {client.data_store_id=} {data_store_ids=} with length: {len(search_response)}")
            else:
                for result in search_response.results:
                    print(f"  - Document: {len(result.document.name)}")

        except Exception as e:
            print(f"Error during search: {e}")

    def test_search_with_filters(client, query, filters=None, data_store_ids=None):
        """
        Performs a search with filters and prints the results.
        """
        try:
            search_response = client.search_with_filters(
                query=query,
                filter_str=filters,
                data_store_ids=data_store_ids,
                #parse_chunks_to_string=False
            )

            print("Search results with filters:")
            if not search_response:
                return f"No results found for {client.data_store_id=}"
            if isinstance(search_response, str):
                print(f"Found search_response for {client.data_store_id=} with length: {len(search_response)} ")
            else:
                print(f"{search_response=}")

        except Exception as e:
            print(f"Error during filtered search: {e}")

    def test_search_with_obj_date(client, query, objectId=None, date=None, data_store_ids=None):
        """
        Performs a search with filters and prints the results.
        """
        try:
            search_response = client.search_by_objectId_and_or_date(
                query=query,
                objectId=objectId,
                date=date,
                data_store_ids=data_store_ids
            )

            print("Search results with objectId and date filters:")
            if not search_response:
                return f"No results found for {client.data_store_id}"
            if isinstance(search_response, str):
                print(f"Found search_response for {client.data_store_id} with length: {len(search_response)}")
            else:
                print("No results")

        except Exception as e:
            print(f"Error during filtered search2: {e}")

    # 1. Test with multiple data stores
    client = DiscoveryEngineClient(data_store_id="aitana", project_id=PROJECT_ID, location=LOCATION)
    test_query = "What is MLOps?"
    print(f"Testing search with multiple data stores: {data_store_ids}")
    test_search(client, test_query, data_store_ids) #working

    data_store_ids = [
        "aitana", #default collection
        #"sunholo-drive-datastore",
        #"sunholo-gmail-datastore_google_mail",
        # Add other data store IDs as needed
    ]
    # 2. Test with a single data store
    for data_store_id in data_store_ids:
        client = DiscoveryEngineClient(data_store_id, project_id=PROJECT_ID, location=LOCATION)
        client.data_store_id = data_store_id  # Set data store ID for the client
        test_query = "What is MLOps?"
        print(f"\nTesting search with single data store: {data_store_id}")
        test_search(client, test_query) #working

        # 3. Test filter by folder
        print(f"\nTesting search for {data_store_id} with folder filter:") #working
        test_search_with_filters(client, test_query, 
                                 filters='objectId: ANY("aitana/practitioners_guide_to_mlops_whitepaper.pdf")')

        # 4. Test filter by date
        print(f"\nTesting search for {data_store_id} with date filter:")
        test_search_with_filters(client, test_query, filters='eventTime >= "2025-01-24"') #working

        # 5. Test filter by folder and date
        print(f"\nTesting search for {data_store_id} with folder and date filter:") #working
        test_search_with_filters(client, test_query, 
                                 filters='objectId: ANY("aitana/practitioners_guide_to_mlops_whitepaper.pdf") AND eventTime >= "2025-01-24"')

        # 6. Test with date filter
        print(f"\n2Testing search for {data_store_id} with date filter:")
        test_search_with_obj_date(client, test_query, date="2025-01-24") #working

        # 7. Test with objectId filter
        print(f"\n2Testing search for {data_store_id} with objectId filter:") #working
        test_search_with_obj_date(client, test_query, objectId="aitana/practitioners_guide_to_mlops_whitepaper.pdf")

        # 8. Test filter by folder and date
        print(f"\n2Testing search for {data_store_id} with folder and date filter:") #working
        test_search_with_obj_date(client, test_query, objectId="aitana/practitioners_guide_to_mlops_whitepaper.pdf", date="2025-01-24")


# Run the tests
#test_discovery_engine_client(PROJECT_ID, LOCATION, DATA_STORE_IDS)