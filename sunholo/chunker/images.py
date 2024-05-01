import base64
import datetime
import tempfile
import os
from ..gcs.add_file import add_file_to_gcs, get_image_file_name
from ..logging import log
from ..utils.gcp import is_running_on_gcp


def upload_doc_images(metadata):
    image_base64 = metadata.get('image_base64')
    # upload an image to the objectId/img folder
    if image_base64 and len(image_base64) > 100:
        image_data = base64.b64decode(image_base64)

        # Determine the file extension based on the MIME type
        mime_type = metadata.get("image_mime_type", "")
        object_id = metadata.get("objectId", "image")
        log.info(f"Found image_base64 for {object_id}")
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        image_path = get_image_file_name(object_id, image_name=timestamp, mime_type=mime_type)
        
        # Write image data to a temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_image:
            temp_image.write(image_data)
            temp_image.flush()  # Make sure all data is written to the file

        temp_image_path = temp_image.name

        # wipe this so it doesn't get stuck in loop
        metadata["image_base64"] = None
        metadata["uploaded_to_bucket"] = True

        if is_running_on_gcp():
            # Use the provided function to upload the file to GCS
            image_gsurl = add_file_to_gcs(
                filename=temp_image_path,
                vector_name=metadata["vector_name"],
                bucket_name=metadata["bucket_name"],
                metadata=metadata,
                bucket_filepath=image_path
            )
            os.remove(temp_image.name)
            log.info(f"Uploaded image to GCS: {image_gsurl}")

            return image_gsurl
        
        else:
            #TODO: other blob storage
            return None

        

