# Creating your own VAC

This is a step by step guide in creating your own VAC.

0. Install via `pip install sunholo`
1. Create a new git repository and browse to the root
1. Run `sunholo init new_project` to create a project called "new_project"
1. This will create a new folder with an example project files.
1. Make your changes to the `vac_service.py` file - specifically the `vac` and `vac_stream` functions

## vac_service.py

This is the guts of your GenAI application.

### Images/Videos

Images can be automatically inserted into your request arguments.

Make a request to upload a new image via a POST form request.  The VAC will then upload that image to a Google Cloud Storage bucket, and return the URL, or if say the endpoint accepts base64 images pass that through.

The image and mime type are then available to your VACs in the `kwargs` via `uri` and `mime`

```python
def vac_stream(question: str, vector_name: str, chat_history=[], callback=None, **kwargs):

...
    url = None
    if kwargs.get('image_uri'):
        log.info(f"Got image_url: {kwargs.get('image_url')}")
        url = kwargs["image_uri"]
    else:
        log.debug("No image_uri found")

    mime = None
    if kwargs.get('mime'):
        log.info(f"Got mime: {kwargs.get('image_url')}")
        mime = kwargs["mime"]
    else:
        log.debug("No mime found")
...
```