import re
from ..utils.mime import guess_mime_type
from ..gcs import get_bytes_from_gcs
from ..custom_logging import log
import io
import os
try:
    import google.generativeai as genai
except ImportError:
    genai = None

def extract_gs_images_and_genai_upload(content:str):
    # Regular expression to find gs:// URLs 
    pattern = r'gs://[^ ]+\.(?:png|jpg|jpeg|pdf)'

    gs_matches = re.findall(pattern, content)
    unique_gs_matches = set(gs_matches)
    output_gs_images = []
    for gs_uri in unique_gs_matches:
        mime_type = guess_mime_type(gs_uri)
        if mime_type is None:
            continue
        
        log.info(f"Getting bytes from GCS: {gs_uri}")
        image_bytes = get_bytes_from_gcs(gs_uri)
        if image_bytes is None:
            continue
        image_file = io.BytesIO(image_bytes)
        image_file.name = os.path.basename(gs_uri)  # Assign a name, as some APIs require it
        
        try:
            uploaded_file = genai.upload_file(image_file)
            output_gs_images.append(uploaded_file)
        
        except Exception as e:
            log.error(f"Error adding {gs_uri} to base64: {str(e)}")
    
    return output_gs_images