from langfuse.callback import CallbackHandler

def create_langfuse_callback():
    langfuse_handler = CallbackHandler()

    # Tests the SDK connection with the server
    langfuse_handler.auth_check()

    return langfuse_handler