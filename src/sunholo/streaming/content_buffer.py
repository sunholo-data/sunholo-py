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
from typing import Any, Dict, List, Union

import threading
import asyncio
import re
from ..custom_logging import log

class ContentBuffer:
    """
    A buffer class for storing and managing textual content.

    This class provides methods to write text to the buffer, read the entire buffer content,
    and clear the buffer content. The buffer can be used to collect text output for further
    processing or inspection.

    Attributes:
        content (str): Stores the textual content of the buffer.
    """

    def __init__(self):
        """
        Initializes a new ContentBuffer instance.

        The content buffer starts with an empty string, and logging is initialized to indicate
        that the buffer has been created.
        """
        self.content = ""
        self.lock = asyncio.Lock()  # Use an async lock to ensure atomic writes
        self.content_available = asyncio.Event()
        log.debug("Content buffer initialized")
    
    def write(self, text: str):
        """
        Writes text to the content buffer.

        Args:
            text (str): The text to be added to the buffer.

        Adds the given text to the existing content of the buffer.
        """
        self.content += text

    async def async_write(self, text: str):
        """
        Asynchronously writes text to the content buffer.

        Args:
            text (str): The text to be added to the buffer.

        Adds the given text to the existing content of the buffer.
        """
        async with self.lock:
            self.content += text
            self.content_available.set()
    
    def read(self) -> str:
        """
        Reads the entire content from the buffer.

        Returns:
            str: The content of the buffer.

        Provides the entire content stored in the buffer.
        """   
        return self.content

    async def async_read(self) -> str:
        """
        Asynchronously reads the entire content from the buffer.

        Returns:
            str: The content of the buffer.
        """
        async with self.lock:
            content = self.content
            return content

    def clear(self):
        """
        Clears the content buffer.

        Empties the buffer content, resetting it to an empty string.
        """
        self.content = ""

    async def async_clear(self):
        """
        Asynchronously clears the content buffer.

        Empties the buffer content, resetting it to an empty string.
        """
        async with self.lock:
            self.content = ""
            self.content_available.clear()


class BufferStreamingStdOutCallbackHandler:
    """
    A callback handler for streaming LLM output to a content buffer.

    This class handles the streaming of output from a large language model (LLM),
    processes tokens from the model output, and writes them to a ContentBuffer.
    It supports handling different types of tokens and keeps track of code blocks
    and questions.

    Attributes:
        content_buffer (ContentBuffer): The buffer to which content is streamed.
        tokens (str): Tokens that indicate the end of a statement, for buffer flushing.
        buffer (str): Temporary storage for accumulating streamed tokens.
        stream_finished (threading.Event): Signals when the streaming is finished.
        in_code_block (bool): Indicates whether the current context is a code block.
        in_question_block (bool): Indicates whether the current context is a question block.
        question_buffer (str): Stores the accumulated questions.
    """

    def __init__(self, content_buffer: ContentBuffer, tokens: str = ".?!\n", *args, **kwargs):
        """
        Initializes a new BufferStreamingStdOutCallbackHandler instance.

        Args:
            content_buffer (ContentBuffer): The buffer to which content will be written.
            tokens (str): Tokens that indicate the end of a statement (default: ".?!\n").
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Sets up the callback handler with the given content buffer and tokens.
        Initializes tracking variables for code blocks, buffer content, and the finished signal.
        """
        super().__init__(*args, **kwargs)
        self.content_buffer = content_buffer
        self.tokens = tokens
        self.buffer = ""
        self.stream_finished = threading.Event()

        self.in_code_block = False
        self.in_question_block = False
        self.question_buffer = ""
        log.info("Starting to stream LLM")

    def _is_heartbeat_token(self, token: str) -> bool:
        """Detects if the token is a heartbeat message."""
        return token.startswith('[[HEARTBEAT]]') and token.endswith('[[/HEARTBEAT]]')

    def _strip_heartbeat_markers(self, token: str) -> str:
        """Removes the [[HEARTBEAT]] markers from the token."""
        return token[len('[[HEARTBEAT]]'):-len('[[/HEARTBEAT]]')]

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """
        Processes a new token from the LLM output.

        Args:
            token (str): The new token generated by the LLM.
            **kwargs: Additional keyword arguments.

        Accumulates the token in the buffer and processes it based on the current context.
        The buffer content is written to the content buffer when appropriate tokens or
        patterns are detected.
        """
        #log.debug(f"on_llm_new_token: {token}")

        # Check if the token is a heartbeat message
        if self._is_heartbeat_token(token):
            # Strip the [[HEARTBEAT]] markers and write immediately
            heartbeat_content = self._strip_heartbeat_markers(token)
            #log.info(f"Heartbeat token detected, writing immediately: {heartbeat_content}")
            self.content_buffer.write(heartbeat_content)
        else:
            self.buffer += token

            if '```' in token:
                self.in_code_block = not self.in_code_block

            if not self.in_code_block:
                self._process_buffer()

    def _process_buffer(self):
        """
        Processes the buffer content and writes to the content buffer.

        If the buffer ends with a numbered list pattern or specified tokens, the buffer is flushed
        to the content buffer. Otherwise, the buffer is left intact for further accumulation.
        """
        matches = list(re.finditer(r'\n(\d+\.\s)', self.buffer))
        if matches:
            last_match = matches[-1]
            start_of_last_match = last_match.start() + 1
            self.content_buffer.write(self.buffer[:start_of_last_match])
            self.buffer = self.buffer[start_of_last_match:]
        else:
            if any(self.buffer.endswith(t) for t in self.tokens):
                self.content_buffer.write(self.buffer)
                self.buffer = ""

    def on_llm_end(self, response, **kwargs: Any) -> None:
        """
        Handles the end of LLM streaming.

        Args:
            response: The result returned by the LLM.
            **kwargs: Additional keyword arguments.

        Writes any remaining buffer content to the content buffer, and sets a signal indicating
        that the streaming has finished.
        """
        if self.buffer:
            self.content_buffer.write(self.buffer)
            self.buffer = ""
            log.info("Flushing remaining LLM response buffer")

        self.stream_finished.set()
        log.info("Streaming LLM response ended successfully")



class BufferStreamingStdOutCallbackHandlerAsync:
    """
    An async callback handler for streaming LLM output to a content buffer.

    This class handles the streaming of output from a large language model (LLM),
    processes tokens from the model output, and writes them to a ContentBuffer.
    It supports handling different types of tokens and keeps track of code blocks
    and questions.

    Attributes:
        content_buffer (ContentBuffer): The buffer to which content is streamed.
        tokens (str): Tokens that indicate the end of a statement, for buffer flushing.
        buffer (str): Temporary storage for accumulating streamed tokens.
        stream_finished (asyncio.Event): Signals when the streaming is finished.
        in_code_block (bool): Indicates whether the current context is a code block.
    """

    def __init__(self, content_buffer: ContentBuffer, tokens: str = ".?!\n", *args, **kwargs):
        """
        Initializes a new BufferStreamingStdOutCallbackHandler instance.

        Args:
            content_buffer (ContentBuffer): The buffer to which content will be written.
            tokens (str): Tokens that indicate the end of a statement (default: ".?!\n").
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Sets up the callback handler with the given content buffer and tokens.
        Initializes tracking variables for code blocks, buffer content, and the finished signal.
        """
        super().__init__(*args, **kwargs)
        self.content_buffer = content_buffer
        self.tokens = tokens
        self.buffer = ""
        self.stream_finished = asyncio.Event()  # Use asyncio.Event for async compatibility
        self.in_code_block = False
        log.info("Starting to stream LLM")

    async def async_on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        #log.debug(f"async_on_llm_new_token: {token}")

        # Check if the token is a heartbeat message
        if self._is_heartbeat_token(token):
            # Strip the [[HEARTBEAT]] markers and write immediately
            heartbeat_content = self._strip_heartbeat_markers(token)
            #log.info(f"Heartbeat token detected, writing immediately: {heartbeat_content}")
            await self.content_buffer.async_write(heartbeat_content)
        else:
            self.buffer += token

            if '```' in token:
                self.in_code_block = not self.in_code_block

            if not self.in_code_block:
                await self._async_process_buffer()

    def _is_heartbeat_token(self, token: str) -> bool:
        """Detects if the token is a heartbeat message."""
        return token.startswith('[[HEARTBEAT]]') and token.endswith('[[/HEARTBEAT]]')

    def _strip_heartbeat_markers(self, token: str) -> str:
        """Removes the [[HEARTBEAT]] markers from the token."""
        return token[len('[[HEARTBEAT]]'):-len('[[/HEARTBEAT]]')]

    async def _async_process_buffer(self):
        """
        Asynchronously processes the buffer content and writes to the content buffer.

        If the buffer ends with a numbered list pattern or specified tokens, the buffer is flushed
        to the content buffer. Otherwise, the buffer is left intact for further accumulation.
        """
        matches = list(re.finditer(r'\n(\d+\.\s)', self.buffer))
        if matches:
            last_match = matches[-1]
            start_of_last_match = last_match.start() + 1
            await self.content_buffer.async_write(self.buffer[:start_of_last_match])
            self.buffer = self.buffer[start_of_last_match:]
        else:
            if any(self.buffer.endswith(t) for t in self.tokens):
                await self.content_buffer.async_write(self.buffer)
                self.buffer = ""

    async def async_on_llm_end(self, response, **kwargs: Any) -> None:
        """
        Asynchronously handles the end of LLM streaming.

        Args:
            response: The result returned by the LLM.
            **kwargs: Additional keyword arguments.
        """
        if self.buffer:
            await self.content_buffer.async_write(self.buffer)
            self.buffer = ""
            log.info("Flushing remaining LLM response buffer")

        self.stream_finished.set()
        log.info("Streaming LLM response ended successfully")

