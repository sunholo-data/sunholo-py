# process_azure_blob_event.py
from ..custom_logging import log

def process_azure_blob_event(events: list) -> tuple:
    """
    Extracts message data and metadata from an Azure Blob Storage event.

    Args:
        events (list): The list of Azure Event Grid event data.

    Returns:
        tuple: A tuple containing the blob URL, attributes as metadata, and the vector name.
        
    Example of Event Grid schema:
    ```
    {
        "topic": "/subscriptions/subscription-id/resourceGroups/resource-group/providers/Microsoft.Storage/storageAccounts/storage-account",
        "subject": "/blobServices/default/containers/container/blobs/blob",
        "eventType": "Microsoft.Storage.BlobCreated",
        "eventTime": "2021-01-01T12:34:56.789Z",
        "id": "event-id",
        "data": {
            "api": "PutBlob",
            "clientRequestId": "client-request-id",
            "requestId": "request-id",
            "eTag": "etag",
            "contentType": "application/octet-stream",
            "contentLength": 524288,
            "blobType": "BlockBlob",
            "url": "https://storage-account.blob.core.windows.net/container/blob",
            "sequencer": "0000000000000000000000000",
            "storageDiagnostics": {
                "batchId": "batch-id"
            }
        },
        "dataVersion": "",
        "metadataVersion": "1"
    }
    ```
    """
    storage_blob_created_event = "Microsoft.Storage.BlobCreated"
    
    for event in events:
        event_type = event['eventType']
        data = event['data']

        if event_type == storage_blob_created_event:
            blob_url = data['url']
            event_time = event['eventTime']
            event_id = event['id']
            subject = event['subject']
            attributes = {
                'event_type': event_type,
                'event_time': event_time,
                'event_id': event_id,
                'subject': subject,
                'url': blob_url
            }

            vector_name = subject.split('/')[4]  # Extracting the container name
            
            log.info(f"Process Azure Blob Event was triggered by eventId {event_id} at {event_time}")
            log.debug(f"Process Azure Blob Event data: {blob_url}")
            
            # Check for a valid Azure Blob Storage event type
            if event_type == "Microsoft.Storage.BlobCreated":
                log.info(f"Got valid event from Azure Blob Storage: {blob_url}")
            
            return blob_url, attributes, vector_name

    return None, None, None