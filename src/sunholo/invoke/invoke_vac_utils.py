import json
import requests

from pathlib import Path

from ..custom_logging import log

def invoke_vac(service_url, data, vector_name=None, metadata=None, is_file=False):
    """
    This lets a VAC be invoked by directly calling its URL, used for file uploads
    """
    try:
        if is_file:
            log.info("Uploading file...")
            # Handle file upload
            if not isinstance(data, Path) or not data.is_file():
                raise ValueError("For file uploads, 'data' must be a Path object pointing to a valid file.")
            
            files = {
                'file': (data.name, open(data, 'rb')),
            }
            form_data = {
                'vector_name': vector_name,
                'metadata': json.dumps(metadata) if metadata else '',
            }

            response = requests.post(service_url, files=files, data=form_data)
        else:
            log.info("Uploading JSON...")
            try:
                if isinstance(data, dict):
                    json_data = data
                else:
                    json_data = json.loads(data)
            except json.JSONDecodeError as err:
                log.error(f"ERROR: invalid JSON: {str(err)}")
                raise err
            except Exception as err:
                log.error(f"ERROR: could not parse JSON: {str(err)}")
                raise err

            log.debug(f"Sending data: {data} or json_data: {json.dumps(json_data)}")
            # Handle JSON data
            headers = {"Content-Type": "application/json"}
            response = requests.post(service_url, headers=headers, data=json.dumps(json_data))

        response.raise_for_status()

        the_data = response.json()
        log.info(the_data)

        return the_data
    
    except requests.exceptions.RequestException as e:
        log.error(f"[bold red]ERROR: Failed to invoke VAC: {e}[/bold red]")
        raise e
    except Exception as e:
        log.error(f"[bold red]ERROR: An unexpected error occurred: {e}[/bold red]")
        raise e
