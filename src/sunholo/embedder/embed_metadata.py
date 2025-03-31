
import datetime
import re

from ..utils.mime import guess_mime_type

from ..custom_logging import log

def audit_metadata(metadata, chunk_length=None):
    
    if 'eventTime' not in metadata:
        metadata['eventTime'] = datetime.datetime.now().isoformat(timespec='microseconds') + "Z"
    metadata['eventtime'] = metadata['eventTime']

    # Extract time-based dimensions from eventTime
    try:
        # Handle timestamps in ISO format with Z suffix
        event_time_str = metadata['eventTime']
        if event_time_str.endswith('Z'):
            event_time_str = event_time_str[:-1]  # Remove the Z suffix
        
        event_time = datetime.datetime.fromisoformat(event_time_str)
        
        # Add year dimension (e.g., 2025)
        metadata['year'] = str(event_time.year)
        # Add yearMonth dimension (e.g., 2025-03)
        metadata['yearMonth'] = f"{event_time.year}-{event_time.month:02d}"
        # Add month dimension (e.g., 03)
        metadata['month'] = f"{event_time.month:02d}"
    except (ValueError, TypeError) as e:
        log.warning(f"Could not parse eventTime for time dimensions: {metadata['eventTime']}, error: {e}")

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

     # Extract folder paths from source field
    if 'source' in metadata and metadata['source']:
        source_path = metadata['source']

        metadata['mime_type'] = guess_mime_type(source_path)

        # Extract file extension
        if '.' in source_path.split('/')[-1]:
            file_extension = source_path.split('/')[-1].split('.')[-1].lower()
            metadata['file_extension'] = file_extension
            
            # Add file type category
            if file_extension in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']:
                metadata['file_type'] = 'document'
            elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'svg']:
                metadata['file_type'] = 'image'
            elif file_extension in ['mp3', 'wav', 'ogg', 'flac', 'm4a']:
                metadata['file_type'] = 'audio'
            elif file_extension in ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm']:
                metadata['file_type'] = 'video'
            elif file_extension in ['xls', 'xlsx', 'csv']:
                metadata['file_type'] = 'spreadsheet'
            elif file_extension in ['ppt', 'pptx']:
                metadata['file_type'] = 'presentation'
            elif file_extension in ['zip', 'rar', 'tar', 'gz', '7z']:
                metadata['file_type'] = 'archive'
            elif file_extension in ['html', 'htm', 'xml', 'json', 'yaml', 'yml']:
                metadata['file_type'] = 'markup'
            elif file_extension in ['py', 'js', 'java', 'c', 'cpp', 'cs', 'go', 'rb', 'php']:
                metadata['file_type'] = 'code'
            else:
                metadata['file_type'] = 'other'
        
        # Check if the source looks like a GCS path
        if source_path.startswith('gs://'):
            # Remove the gs:// prefix
            path_without_prefix = source_path[5:]
            
            # Split the path into components
            path_components = path_without_prefix.split('/')
            
            # The first component is the bucket name
            if len(path_components) > 0:
                metadata['bucket_name'] = path_components[0]
            
            # Extract up to 5 folder levels
            for i in range(1, min(6, len(path_components))):
                if i < len(path_components) - 1:  # Skip the last component (filename)
                    folder_key = f'folder_{i}'
                    metadata[folder_key] = path_components[i]
            
            # Extract the object name (last component)
            if len(path_components) > 1:
                metadata['object_name'] = path_components[-1]
        
        # For other URL types, try to extract paths
        elif re.match(r'^(http|https|s3|file)://', source_path):
            # Extract path part after domain
            match = re.search(r'://[^/]+/(.+)', source_path)
            if match:
                path_part = match.group(1)
                path_components = path_part.split('/')
                
                # Extract up to 5 folder levels
                for i in range(0, min(5, len(path_components) - 1)):
                    folder_key = f'folder_{i+1}'
                    metadata[folder_key] = path_components[i]
                
                # Extract the object name (last component)
                if path_components:
                    metadata['object_name'] = path_components[-1]

    # Add file size category if size exists
    if 'size' in metadata and isinstance(metadata['size'], (int, float)):
        size_bytes = metadata['size']
        if size_bytes < 10 * 1024:  # < 10KB
            metadata['size_category'] = 'tiny'
        elif size_bytes < 1024 * 1024:  # < 1MB
            metadata['size_category'] = 'small'
        elif size_bytes < 10 * 1024 * 1024:  # < 10MB
            metadata['size_category'] = 'medium'
        elif size_bytes < 100 * 1024 * 1024:  # < 100MB
            metadata['size_category'] = 'large'
        else:  # >= 100MB
            metadata['size_category'] = 'very_large'

    # Add day of week
    try:
        if 'eventTime' in metadata:
            event_time_str = metadata['eventTime']
            if event_time_str.endswith('Z'):
                event_time_str = event_time_str[:-1]
            
            event_time = datetime.datetime.fromisoformat(event_time_str)
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            metadata['day_of_week'] = weekday_names[event_time.weekday()]
            
            # Add quarter information
            quarter = (event_time.month - 1) // 3 + 1
            metadata['quarter'] = f"Q{quarter}"
            metadata['yearQuarter'] = f"{event_time.year}-Q{quarter}"
    except (ValueError, TypeError) as e:
        log.warning(f"Could not extract additional time metadata: {e}")
    
    return metadata
