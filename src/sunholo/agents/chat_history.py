import json
from ..custom_logging import log
import time
import hashlib
from functools import lru_cache
from typing import List, Tuple, Optional


class ChatHistoryCache:
    """
    Incremental cache for chat history processing.
    
    Caches processed message pairs and only processes new messages
    when the chat history is extended.
    """
    
    def __init__(self, max_cache_size: int = 1000):
        self.cache = {}
        self.max_cache_size = max_cache_size
    
    def _get_cache_key(self, chat_history: List[dict]) -> str:
        """Generate a cache key based on the chat history content."""
        # Use the hash of the serialized chat history for the key
        # Only hash the first few and last few messages to balance performance vs accuracy
        if len(chat_history) <= 10:
            content = str(chat_history)
        else:
            # Hash first 5 and last 5 messages + length
            content = str(chat_history[:5] + chat_history[-5:] + [len(chat_history)])
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _find_cached_prefix(self, current_history: List[dict]) -> Tuple[Optional[List[Tuple]], int]:
        """
        Find the longest cached prefix of the current chat history.
        
        Returns:
            Tuple of (cached_pairs, cache_length) or (None, 0) if no cache found
        """
        current_length = len(current_history)
        
        # Check for cached versions of prefixes, starting from longest
        for cache_length in range(current_length - 1, 0, -1):
            prefix = current_history[:cache_length]
            cache_key = self._get_cache_key(prefix)
            
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                cached_pairs = cached_data['pairs']
                
                # Verify the cache is still valid by checking a few messages
                if self._verify_cache_validity(prefix, cached_data['original_history']):
                    return cached_pairs, cache_length
                else:
                    # Cache is stale, remove it
                    del self.cache[cache_key]
        
        return None, 0
    
    def _verify_cache_validity(self, current_prefix: List[dict], cached_prefix: List[dict]) -> bool:
        """Quick verification that cached data is still valid."""
        if len(current_prefix) != len(cached_prefix):
            return False
        
        # Check first and last few messages for equality
        check_indices = [0, -1] if len(current_prefix) >= 2 else [0]
        
        for i in check_indices:
            if current_prefix[i] != cached_prefix[i]:
                return False
        
        return True
    
    def extract_chat_history_incremental(self, chat_history: List[dict]) -> List[Tuple]:
        """
        Extract chat history with incremental caching.
        
        Args:
            chat_history: List of chat message dictionaries
            
        Returns:
            List of (human_message, ai_message) tuples
        """
        if not chat_history:
            return []
        
        # Try to find cached prefix
        cached_pairs, cache_length = self._find_cached_prefix(chat_history)
        
        if cached_pairs is not None:
            log.debug(f"Found cached pairs for {cache_length} messages, processing {len(chat_history) - cache_length} new messages")
            
            # Process only the new messages
            new_messages = chat_history[cache_length:]
            new_pairs = self._process_new_messages(new_messages, cached_pairs)
            
            # Combine cached and new pairs
            all_pairs = cached_pairs + new_pairs
        else:
            log.debug(f"No cache found, processing all {len(chat_history)} messages")
            # Process all messages from scratch
            all_pairs = self._extract_chat_history_full(chat_history)
        
        # Cache the result
        self._update_cache(chat_history, all_pairs)
        
        return all_pairs
    
    def _process_new_messages(self, new_messages: List[dict], cached_pairs: List[Tuple]) -> List[Tuple]:
        """
        Process only the new messages, considering the state from cached pairs.
        
        Args:
            new_messages: New messages to process
            cached_pairs: Previously processed message pairs
            
        Returns:
            List of new message pairs
        """
        if not new_messages:
            return []
        
        new_pairs = []
        
        # Determine if we're waiting for a bot response based on cached pairs
        waiting_for_bot = True
        if cached_pairs:
            last_pair = cached_pairs[-1]
            # If last pair has both human and AI message, we're ready for a new human message
            waiting_for_bot = not (last_pair[0] and last_pair[1])
        
        # If we ended with an unpaired human message, get it
        last_human_message = ""
        if cached_pairs and waiting_for_bot:
            last_human_message = cached_pairs[-1][0]
        
        # Process new messages
        for message in new_messages:
            try:
                is_human_msg = is_human(message)
                content = create_message_element(message)
                
                if is_human_msg:
                    last_human_message = content
                    waiting_for_bot = True
                else:  # Bot message
                    if waiting_for_bot and last_human_message:
                        new_pairs.append((last_human_message, content))
                        last_human_message = ""
                        waiting_for_bot = False
                    # If not waiting for bot or no human message, this is an orphaned bot message
                    
            except (KeyError, TypeError) as e:
                log.warning(f"Error processing new message: {e}")
                continue
        
        return new_pairs
    
    def _extract_chat_history_full(self, chat_history: List[dict]) -> List[Tuple]:
        """Full extraction when no cache is available."""
        # Use the optimized version from before
        paired_messages = []
        
        # Handle initial bot message
        start_idx = 0
        if chat_history and is_bot(chat_history[0]):
            try:
                first_message = chat_history[0]
                blank_element = ""
                bot_element = create_message_element(first_message)
                paired_messages.append((blank_element, bot_element))
                start_idx = 1
            except (KeyError, TypeError):
                pass
        
        # Process remaining messages
        last_human_message = ""
        for i in range(start_idx, len(chat_history)):
            message = chat_history[i]
            
            try:
                is_human_msg = is_human(message)
                content = create_message_element(message)
                
                if is_human_msg:
                    last_human_message = content
                else:  # Bot message
                    if last_human_message:
                        paired_messages.append((last_human_message, content))
                        last_human_message = ""
                        
            except (KeyError, TypeError) as e:
                log.warning(f"Error processing message {i}: {e}")
                continue
        
        return paired_messages
    
    def _update_cache(self, chat_history: List[dict], pairs: List[Tuple]):
        """Update cache with new result."""
        # Only cache if the history is of reasonable size
        if len(chat_history) < 2:
            return
        
        cache_key = self._get_cache_key(chat_history)
        
        # Implement simple LRU by removing oldest entries
        if len(self.cache) >= self.max_cache_size:
            # Remove 20% of oldest entries
            remove_count = self.max_cache_size // 5
            oldest_keys = list(self.cache.keys())[:remove_count]
            for key in oldest_keys:
                del self.cache[key]
        
        self.cache[cache_key] = {
            'pairs': pairs,
            'original_history': chat_history.copy(),  # Store copy for validation
            'timestamp': time.time()
        }
        
        log.debug(f"Cached {len(pairs)} pairs for history of length {len(chat_history)}")
    
    def clear_cache(self):
        """Clear the entire cache."""
        self.cache.clear()
        log.info("Chat history cache cleared")


# Global cache instance
_chat_history_cache = ChatHistoryCache()


def extract_chat_history_with_cache(chat_history: List[dict] = None) -> List[Tuple]:
    """
    Main function to replace the original extract_chat_history.
    
    Uses incremental caching for better performance with growing chat histories.
    """
    if not chat_history:
        log.debug("No chat history found")
        return []
    
    return _chat_history_cache.extract_chat_history_incremental(chat_history)


# Async version that wraps the cached version
async def extract_chat_history_async_cached(chat_history: List[dict] = None) -> List[Tuple]:
    """
    Async version that uses the cache and runs in a thread pool if needed.
    """
    import asyncio
    
    if not chat_history:
        return []
    
    # For very large histories, run in thread pool to avoid blocking
    if len(chat_history) > 1000:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            extract_chat_history_with_cache, 
            chat_history
        )
    else:
        # For smaller histories, just run directly
        return extract_chat_history_with_cache(chat_history)


# Utility function to warm up the cache
def warm_up_cache(chat_histories: List[List[dict]]):
    """
    Pre-populate cache with common chat histories.
    
    Args:
        chat_histories: List of chat history lists to cache
    """
    for history in chat_histories:
        extract_chat_history_with_cache(history)
    
    log.info(f"Warmed up cache with {len(chat_histories)} chat histories")


async def extract_chat_history_async(chat_history=None):
    """
    Extracts paired chat history between human and AI messages.
    
    For this lightweight processing, we use a simpler approach that minimizes overhead.
    
    Args:
        chat_history (list): List of chat messages.
    
    Returns:
        list: List of tuples with paired human and AI messages.
    """
    if not chat_history:
        log.info("No chat history found")
        return []

    log.info(f"Extracting chat history: {chat_history}")
    paired_messages = []
    
    # Handle special case of initial bot message
    if chat_history and is_bot(chat_history[0]):
        first_message = chat_history[0]
        log.info(f"Extracting first_message: {first_message}")
        blank_human_message = {"name": "Human", "content": "", "embeds": []}
        
        # Since create_message_element is so lightweight, we don't need async here
        blank_element = create_message_element(blank_human_message)
        bot_element = create_message_element(first_message)
        
        paired_messages.append((blank_element, bot_element))
        chat_history = chat_history[1:]
    
    # Pre-process all messages in one batch (more efficient than one-by-one)
    message_types = []
    message_contents = []
    
    for message in chat_history:
        is_human_msg = is_human(message)
        is_bot_msg = is_bot(message)
        
        # Extract content for all messages at once
        content = create_message_element(message)
        
        message_types.append((is_human_msg, is_bot_msg))
        message_contents.append(content)
    
    # Pair messages efficiently
    last_human_message = ""
    for i, ((is_human_msg, is_bot_msg), content) in enumerate(zip(message_types, message_contents)):
        if is_human_msg:
            last_human_message = content
            log.info(f"Extracted human message: {last_human_message}")
        elif is_bot_msg:
            ai_message = content
            log.info(f"Extracted AI message: {ai_message}")
            paired_messages.append((last_human_message, ai_message))
            last_human_message = ""
    
    log.info(f"Paired messages: {paired_messages}")
    return paired_messages


def extract_chat_history(chat_history=None):
    """
    Extracts paired chat history between human and AI messages.

    This function takes a chat history and returns a list of pairs of messages,
    where each pair consists of a human message followed by the corresponding AI response.

    Args:
        chat_history (list): List of chat messages.

    Returns:
        list: List of tuples with paired human and AI messages.

    Example:
    ```python
    chat_history = [
        {"name": "Human", "text": "Hello, AI!"},
        {"name": "AI", "text": "Hello, Human! How can I help you today?"}
    ]
    paired_messages = extract_chat_history(chat_history)
    print(paired_messages)
    # Output: [("Hello, AI!", "Hello, Human! How can I help you today?")]
    ```
    """
    if not chat_history:
        log.info("No chat history found")
        return []

    log.info(f"Extracting chat history: {chat_history}")
    paired_messages = []

    first_message = chat_history[0]
    log.info(f"Extracting first_message: {first_message}")
    if is_bot(first_message):
        blank_human_message = {"name": "Human", "content": "", "embeds": []}
        paired_messages.append((create_message_element(blank_human_message), 
                                create_message_element(first_message)))
        chat_history = chat_history[1:]

    last_human_message = ""
    for message in chat_history:
        log.info(f"Extracing message: {message}")
        if is_human(message):
            last_human_message = create_message_element(message)
            log.info(f"Extracted human message: {last_human_message}")
        elif is_bot(message):
            ai_message = create_message_element(message)
            log.info(f"Extracted AI message: {ai_message}")
            paired_messages.append((last_human_message, ai_message))
            last_human_message = ""

    log.info(f"Paired messages: {paired_messages}")

    return paired_messages

def embeds_to_json(message: dict):
    """
    Converts the 'embeds' field in a message to a JSON string.

    Args:
        message (dict): The message containing the 'embeds' field.

    Returns:
        str: JSON string representation of the 'embeds' field or an empty string if no embeds are found.

    Example:
    ```python
    message = {"embeds": [{"type": "image", "url": "https://example.com/image.png"}]}
    json_string = embeds_to_json(message)
    print(json_string)
    # Output: '[{"type": "image", "url": "https://example.com/image.png"}]'
    ```
    """
    if 'embeds' in message and len(message['embeds']) > 0:
        return json.dumps(message.get("embeds"))
    else:
        return ""

def create_message_element(message: dict):
    """
    Extracts the main content of a message.

    Args:
        message (dict): The message to extract content from.

    Returns:
        str: The text or content of the message.

    Raises:
        KeyError: If neither 'content' nor 'text' fields are found.

    Example:
    ```python
    message = {"text": "Hello, AI!"}
    content = create_message_element(message)
    print(content)
    # Output: 'Hello, AI!'
    ```
    """
    if 'text' in message:  # This is a Slack or Google Chat message
        #log.info(f"Found text element - {message['text']}")
        return message['text']
    elif 'content' in message: # Discord or OpenAI history message
        #log.info(f"Found content element - {message['content']}")
        return message['content']
    else:  
        raise KeyError(f"Could not extract 'content' or 'text' element from message: {message}, {type(message)}")

def is_human(message: dict):
    """
    Checks if a message was sent by a human.

    Args:
        message (dict): The message to check.

    Returns:
        bool: True if the message was sent by a human, otherwise False.

    Example:
    ```python
    message = {"name": "Human"}
    print(is_human(message))
    # Output: True
    ```
    """
    if 'name' in message:
        return message["name"] == "Human"
    elif 'sender' in message:  # Google Chat
        return message['sender']['type'] == 'HUMAN'
    elif 'role' in message:
        return message['role'] == 'user'
    else:
        # Slack: Check for the 'user' field and absence of 'bot_id' field
        return 'user' in message and 'bot_id' not in message

def is_bot(message: dict):
    """
    Checks if a message was sent by a bot.

    Args:
        message (dict): The message to check.

    Returns:
        bool: True if the message was sent by a bot, otherwise False.

    Example:
    ```python
    message = {"name": "AI"}
    print(is_bot(message))
    # Output: True
    ```
    """
    return not is_human(message)

def is_ai(message: dict):
    """
    Checks if a message was specifically sent by an AI.

    Args:
        message (dict): The message to check.

    Returns:
        bool: True if the message was sent by an AI, otherwise False.

    Example:
    ```python
    message = {"name": "AI"}
    print(is_ai(message))
    # Output: True
    ```
    """
    if 'name' in message:
        return message["name"] == "AI"
    elif 'sender' in message:  # Google Chat
        return message['sender']['type'] == 'BOT'
    elif 'role' in message:
        return message['role'] == 'assistant'
    else:
        return 'bot_id' in message  # Slack

