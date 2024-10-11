import re
from ..utils.mime import guess_mime_type
from ..gcs import get_bytes_from_gcs
from ..custom_logging import log
import os
import tempfile
try:
    import google.generativeai as genai
except ImportError:
    genai = None

def extract_gs_images_and_genai_upload(content: str, limit:int=20):
    # Regular expression to find gs:// URLs 
    pattern = r'gs://[^ ]+\.(?:png|jpg|jpeg|pdf)'

    gs_matches = re.findall(pattern, content)
    # only 20 images by default
    unique_gs_matches = list(set(gs_matches))[:limit] 
    output_gs_images = []
    
    for gs_uri in unique_gs_matches:
        mime_type = guess_mime_type(gs_uri)
        if mime_type is None:
            continue
        
        log.info(f"Getting bytes from GCS: {gs_uri}")
        image_bytes = get_bytes_from_gcs(gs_uri)
        if image_bytes is None:
            continue

        # Get the basename from the gs_uri to use as the file name
        file_name = os.path.basename(gs_uri)

        # Create a temporary directory and write the file with the basename
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, file_name)
            
            # Write the BytesIO object to the file
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(image_bytes)

            # Pass the temporary file's path to the upload function
            try:
                uploaded_file = genai.upload_file(temp_file_path)
                output_gs_images.append(uploaded_file)
            except Exception as e:
                log.error(f"Error adding {gs_uri} to base64: {str(e)}")
    
    return output_gs_images
