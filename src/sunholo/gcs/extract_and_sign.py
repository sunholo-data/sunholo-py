import re
import asyncio

from .download_url import construct_download_link
from ..utils.mime import guess_mime_type
from ..custom_logging import log

async def extract_gs_uris_and_sign(content, pattern=r'gs://[^\n]+\.(?:png|jpg|jpeg|pdf|txt|md)'):

    gs_matches = re.findall(pattern, content)
    unique_gs_matches = set(gs_matches)
    image_signed_urls = []
    if unique_gs_matches:
        log.info(f"Got gs matches: {unique_gs_matches}")

        async def process_link(gs_url):
            log.info(f"Processing {gs_url}")
            link, encoded_filename, signed = await asyncio.to_thread(construct_download_link, gs_url)
            if signed:
                try:
                    mime_type = guess_mime_type(gs_url)
                except Exception as err:
                    log.error(f"Could not find mime_type for {link} - {str(err)}")
                    mime_type = "application/octet-stream"
                    
                return {
                    "original": gs_url,
                    "link": link,
                    "name": encoded_filename,
                    "mime": mime_type,
                    "signed": signed
                }
            else:
                log.info(f"Could not sign this GS_URI: {gs_url} - skipping")
                return None

        # Gather all tasks and run them concurrently
        image_signed_urls = await asyncio.gather(*(process_link(gs_url) for gs_url in unique_gs_matches))

    log.info(f"found files to msg: {image_signed_urls}")
    return image_signed_urls