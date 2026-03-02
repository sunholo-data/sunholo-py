#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
LiteLLM compatibility fixes for ADK.

Fixes issues when using ADK with non-Google models via LiteLLM, especially
Azure OpenAI which has stricter validation than the direct OpenAI API.

Key fixes:
- Null tool_call.id: Azure requires non-null string IDs for all tool calls.
  ADK's LiteLlm sometimes passes null IDs which Azure rejects.
- Text artifact encoding: LiteLLM's _get_content() only handles inline_data
  for images/video/audio. Text files loaded via load_artifacts_tool come as
  inline_data which needs conversion to text parts.
- PDF extraction: Converts PDF inline_data to extracted text.

Usage:
    from sunholo.adk.litellm_compat import FixedLiteLlm

    model = FixedLiteLlm(
        model="azure/gpt-4o",
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    agent = Agent(model=model, tools=[load_artifacts_tool], ...)
"""
from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, AsyncGenerator, List, Optional

if TYPE_CHECKING:
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.llm_response import LlmResponse
    from litellm import Message

try:
    from google.adk.models.lite_llm import LiteLlm, _get_completion_inputs
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types
    from litellm import ChatCompletionAssistantMessage
    ADK_LITELLM_AVAILABLE = True
except ImportError:
    ADK_LITELLM_AVAILABLE = False

logger = logging.getLogger(__name__)

# MIME types that represent text content
TEXT_MIME_PREFIXES = [
    "text/",
    "application/json",
    "application/xml",
    "application/javascript",
    "application/x-yaml",
]


def _check_deps():
    if not ADK_LITELLM_AVAILABLE:
        raise ImportError(
            "google-adk and litellm are required. "
            "Install with: pip install sunholo[adk]"
        )


def generate_tool_call_id() -> str:
    """Generate a unique tool call ID compatible with Azure OpenAI.

    Format: call_<24-character-hex>

    Returns:
        A unique tool call ID string.
    """
    return f"call_{uuid.uuid4().hex[:24]}"


def is_text_mime_type(mime_type: str) -> bool:
    """Check if a MIME type represents text content.

    Args:
        mime_type: The MIME type to check.

    Returns:
        True if the MIME type represents text content.
    """
    return any(mime_type.startswith(prefix) for prefix in TEXT_MIME_PREFIXES)


def fix_null_tool_call_ids(messages: List) -> List:
    """Fix null tool_call.id values in a list of messages.

    Azure OpenAI requires all tool_call IDs to be non-null strings.
    This function generates UUIDs for any tool calls with null IDs.

    Args:
        messages: List of LiteLLM Message objects.

    Returns:
        List of messages with all null tool_call IDs replaced.
    """
    fixed_count = 0

    for message in messages:
        # Dict-style messages
        if isinstance(message, dict) and message.get("role") == "assistant":
            tool_calls = message.get("tool_calls")
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.get("id") is None:
                        tool_call["id"] = generate_tool_call_id()
                        fixed_count += 1
        # Pydantic model messages
        elif hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if hasattr(tool_call, "id") and tool_call.id is None:
                    tool_call.id = generate_tool_call_id()
                    fixed_count += 1

    if fixed_count > 0:
        logger.info("Fixed %d null tool_call.id value(s) for Azure compatibility", fixed_count)

    return messages


def convert_text_artifacts(llm_request: LlmRequest) -> None:
    """Convert text file artifacts from inline_data to text parts.

    LiteLLM's _get_content() only supports inline_data for images, videos,
    and audio. Text files and PDFs loaded by load_artifacts_tool come as
    inline_data which causes issues. This converts them to text parts.

    Args:
        llm_request: The LlmRequest to modify in-place.
    """
    _check_deps()
    if not llm_request.contents:
        return

    for content in llm_request.contents:
        if not content.parts:
            continue

        new_parts = []
        for part in content.parts:
            if part.inline_data and part.inline_data.data and part.inline_data.mime_type:
                mime = part.inline_data.mime_type

                if is_text_mime_type(mime):
                    try:
                        text_content = part.inline_data.data.decode("utf-8")
                        new_parts.append(types.Part.from_text(text=text_content))
                        logger.debug("Converted text artifact (MIME: %s) to text part", mime)
                    except (UnicodeDecodeError, AttributeError):
                        new_parts.append(part)

                elif mime == "application/pdf":
                    try:
                        text_content = extract_pdf_text(part.inline_data.data)
                        new_parts.append(types.Part.from_text(text=text_content))
                        logger.info("Extracted text from PDF artifact")
                    except Exception as e:
                        logger.warning("PDF text extraction failed: %s", e)
                        new_parts.append(types.Part.from_text(
                            text="[PDF file uploaded but text extraction failed.]"
                        ))
                else:
                    new_parts.append(part)
            else:
                new_parts.append(part)

        content.parts = new_parts


def extract_pdf_text(pdf_data: bytes) -> str:
    """Extract text content from PDF binary data.

    Args:
        pdf_data: The PDF file as bytes.

    Returns:
        Extracted text from all pages.

    Raises:
        ImportError: If pypdf is not installed.
        Exception: If PDF parsing fails.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "pypdf is required for PDF text extraction. "
            "Install with: pip install pypdf"
        )

    import io
    reader = PdfReader(io.BytesIO(pdf_data))

    text_parts = []
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            text_parts.append(f"--- Page {page_num} ---\n{page_text}")

    if not text_parts:
        return "[PDF file contains no extractable text]"

    return "\n\n".join(text_parts)


if ADK_LITELLM_AVAILABLE:
    class FixedLiteLlm(LiteLlm):
        """LiteLLM wrapper with Azure OpenAI compatibility fixes.

        Fixes null tool_call.id values and converts text artifacts
        before sending to LiteLLM, enabling load_artifacts_tool and
        other ADK built-in tools to work with Azure OpenAI.

        Args:
            model: LiteLLM model name (e.g. "azure/gpt-4o").
            **kwargs: Additional arguments passed to LiteLlm.
        """

        async def generate_content_async(
            self, llm_request: LlmRequest, stream: bool = True
        ) -> AsyncGenerator[LlmResponse, None]:
            """Generate content with null tool_call.id fix and text artifact conversion.

            Args:
                llm_request: The request to send.
                stream: Whether to stream the response.

            Yields:
                LlmResponse objects.
            """
            # Convert text artifacts before processing
            convert_text_artifacts(llm_request)

            # Let parent class handle initial request preparation
            self._maybe_append_user_content(llm_request)

            # Get formatted messages
            messages, tools, response_format, generation_params = (
                await _get_completion_inputs(llm_request, self.model)
            )

            # Fix null tool_call IDs
            messages = fix_null_tool_call_ids(messages)

            # Build completion args
            if "functions" in self._additional_args:
                tools = None

            completion_args = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "response_format": response_format,
            }
            completion_args.update(self._additional_args)

            if generation_params:
                completion_args.update(generation_params)

            if stream:
                from google.adk.models.lite_llm import (
                    _model_response_to_chunk,
                    _message_to_generate_content_response,
                    FunctionChunk,
                    TextChunk,
                    UsageMetadataChunk,
                )
                import json

                text = ""
                function_calls = {}
                completion_args["stream"] = True
                usage_metadata = None
                fallback_index = 0

                async for part in await self.llm_client.acompletion(**completion_args):
                    for chunk, finish_reason in _model_response_to_chunk(part):
                        if isinstance(chunk, FunctionChunk):
                            index = chunk.index or fallback_index
                            if index not in function_calls:
                                function_calls[index] = {"name": "", "args": "", "id": None}

                            if chunk.name:
                                function_calls[index]["name"] += chunk.name
                            if chunk.args:
                                function_calls[index]["args"] += chunk.args
                                try:
                                    json.loads(function_calls[index]["args"])
                                    fallback_index += 1
                                except json.JSONDecodeError:
                                    pass

                            function_calls[index]["id"] = (
                                chunk.id
                                or function_calls[index]["id"]
                                or generate_tool_call_id()
                            )
                        elif isinstance(chunk, TextChunk):
                            text += chunk.text
                            yield _message_to_generate_content_response(
                                ChatCompletionAssistantMessage(
                                    role="assistant", content=chunk.text,
                                ),
                                is_partial=True,
                            )
                        elif isinstance(chunk, UsageMetadataChunk):
                            usage_metadata = types.GenerateContentResponseUsageMetadata(
                                prompt_token_count=chunk.prompt_tokens,
                                candidates_token_count=chunk.completion_tokens,
                                total_token_count=chunk.total_tokens,
                            )

                        if (
                            finish_reason in ("tool_calls", "stop")
                        ) and function_calls:
                            from litellm import ChatCompletionMessageToolCall, Function

                            tool_calls_list = []
                            for idx, func_data in function_calls.items():
                                if func_data["id"]:
                                    tool_calls_list.append(
                                        ChatCompletionMessageToolCall(
                                            type="function",
                                            id=func_data["id"],
                                            function=Function(
                                                name=func_data["name"],
                                                arguments=func_data["args"],
                                                index=idx,
                                            ),
                                        )
                                    )
                            resp = _message_to_generate_content_response(
                                ChatCompletionAssistantMessage(
                                    role="assistant",
                                    content=text if text else None,
                                    tool_calls=tool_calls_list if tool_calls_list else None,
                                ),
                                is_partial=False,
                            )
                            if usage_metadata:
                                resp.usage_metadata = usage_metadata
                            yield resp

                        if finish_reason == "stop" and not function_calls:
                            resp = _message_to_generate_content_response(
                                ChatCompletionAssistantMessage(
                                    role="assistant",
                                    content=text if text else None,
                                ),
                                is_partial=False,
                            )
                            if usage_metadata:
                                resp.usage_metadata = usage_metadata
                            yield resp
            else:
                from google.adk.models.lite_llm import _model_response_to_generate_content_response
                result = await self.llm_client.acompletion(**completion_args)
                yield _model_response_to_generate_content_response(result)
