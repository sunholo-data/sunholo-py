
from typing import Dict, Any
from ..custom_logging import log

try:
    from langfuse.callback import CallbackHandler
except ImportError:
    CallbackHandler = None

from ..utils.version import sunholo_version

def create_langfuse_callback(**kwargs):

    if not CallbackHandler:
        log.warning("No CallbackHandler found, install langfuse? `pip install langfuse`")
        return None

    # TODO: maybe use langfuse.trace here instead later
    langfuse_handler = CallbackHandler(**kwargs)

    return langfuse_handler

def add_langfuse_tracing(
        config: Dict[str, Any],
        request) -> Dict[str, Any]:
    """
    Config modifier function to add a tracing callback
    By @jmaness https://github.com/langchain-ai/langserve/issues/311

    :param config: config dict
    :param request: HTTP request
    :return: updated config
    """


    log.debug(f"add_langfuse_tracing config: {config} {request}")

    if "callbacks" not in config:
        config["callbacks"] = []

    user_id = request.headers.get("X-User-ID")
    session_id = request.headers.get("X-Session-ID")
    message_source = request.headers.get("X-Message-Source")

    tags = [sunholo_version()]
    if message_source:
        tags.append(message_source)

    log.info(f"Adding langfuse tags to trace: {tags}")
    langfuse_handler = create_langfuse_callback(
        user_id = user_id,
        session_id = session_id,
        tags = tags
    )
    config["callbacks"].extend([langfuse_handler])

    log.debug(f"add_langfuse_tracing modified config {config}")
    return config


#add_routes(app, my_chain,
#           path="/my-chain",
#           per_req_config_modifier=add_langfuse_tracing)