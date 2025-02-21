
import datetime
from ..custom_logging import log

def audit_metadata(metadata, chunk_length=None):
    
    if 'eventTime' not in metadata:
        metadata['eventTime'] = datetime.datetime.now().isoformat(timespec='microseconds') + "Z"
    metadata['eventtime'] = metadata['eventTime']

    if 'source' not in metadata:
        if 'objectId' in metadata:
            metadata['source'] = metadata['objectId']
        elif 'url' in metadata:
            metadata['source'] = metadata['url']
        else:
            log.warning(f"No source found in metadata: {metadata}")
    
    if 'original_source' not in metadata:
        metadata['original_source'] = metadata.get('source')
    else:
        metadata['source'] = metadata['original_source']
    
    if 'chunk_length' not in metadata:
        metadata['chunk_length'] = chunk_length
    
    return metadata
