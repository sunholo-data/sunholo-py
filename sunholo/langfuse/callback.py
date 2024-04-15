from langfuse.callback import CallbackHandler
from fastapi import Request
from typing import Dict, Any
from ..logging import log

def create_langfuse_callback(**kwargs):

    # TODO: maybe use langfuse.trace here instead later
    langfuse_handler = CallbackHandler(**kwargs)

    return langfuse_handler

def add_langfuse_tracing(
        config: Dict[str, Any],
        request: Request) -> Dict[str, Any]:
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

    # can't import tags yet via CallbackHandler
    from importlib.metadata import version
    package_version = version('sunholo')
    tags = [f"sunholo-v{package_version}"]
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