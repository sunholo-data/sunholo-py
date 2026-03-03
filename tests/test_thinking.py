"""Tests for sunholo.genai.thinking module."""
import pytest

from sunholo.genai.thinking import (
    ThinkingCapture,
    ThinkingContent,
    extract_thinking,
    extract_thinking_simple,
    extract_anthropic_thinking,
    create_thinking_callback,
)


class TestExtractThinking:
    def test_no_thinking_tags(self):
        contents, cleaned = extract_thinking("Just a normal response.")
        assert contents == []
        assert cleaned == "Just a normal response."

    def test_empty_text(self):
        contents, cleaned = extract_thinking("")
        assert contents == []
        assert cleaned == ""

    def test_single_thinking_tag(self):
        text = "<thinking>I need to consider this carefully.</thinking>The answer is 42."
        contents, cleaned = extract_thinking(text)
        assert len(contents) == 1
        assert contents[0].text == "I need to consider this carefully."
        assert contents[0].tag_type == "thinking"
        assert "The answer is 42." in cleaned
        assert "<thinking>" not in cleaned

    def test_multiple_thinking_tags(self):
        text = (
            "<thinking>First thought.</thinking>"
            "Some text."
            "<thinking>Second thought.</thinking>"
            "More text."
        )
        contents, cleaned = extract_thinking(text)
        assert len(contents) == 2
        assert contents[0].text == "First thought."
        assert contents[1].text == "Second thought."
        assert "Some text." in cleaned
        assert "More text." in cleaned

    def test_ant_thinking_tag(self):
        text = "<antThinking>Deep analysis here.</antThinking>Response."
        contents, cleaned = extract_thinking(text)
        assert len(contents) == 1
        assert contents[0].tag_type == "antThinking"
        assert contents[0].text == "Deep analysis here."

    def test_reflection_tag(self):
        text = "<reflection>Let me reconsider.</reflection>Updated answer."
        contents, cleaned = extract_thinking(text)
        assert len(contents) == 1
        assert contents[0].tag_type == "reflection"

    def test_multiline_thinking(self):
        text = "<thinking>\nLine 1\nLine 2\nLine 3\n</thinking>Response."
        contents, cleaned = extract_thinking(text)
        assert len(contents) == 1
        assert "Line 1" in contents[0].text
        assert "Line 2" in contents[0].text

    def test_no_tag_removal(self):
        text = "<thinking>Thoughts.</thinking>Answer."
        contents, cleaned = extract_thinking(text, remove_tags=False)
        assert len(contents) == 1
        assert "<thinking>" in cleaned


class TestExtractThinkingSimple:
    def test_simple_extraction(self):
        text = "<thinking>My thoughts.</thinking>The answer."
        thinking, response = extract_thinking_simple(text)
        assert thinking == "My thoughts."
        assert "The answer." in response

    def test_no_thinking(self):
        thinking, response = extract_thinking_simple("Just a response.")
        assert thinking == ""
        assert response == "Just a response."

    def test_multiple_sections_joined(self):
        text = "<thinking>A</thinking>mid<thinking>B</thinking>end"
        thinking, response = extract_thinking_simple(text)
        assert "A" in thinking
        assert "B" in thinking


class TestThinkingCapture:
    def test_no_thinking_in_stream(self):
        capture = ThinkingCapture()
        result = capture.process_chunk("Hello world")
        assert result == "Hello world"
        assert capture.get_thinking() == ""
        assert capture.get_response() == "Hello world"

    def test_thinking_in_single_chunk(self):
        capture = ThinkingCapture()
        result = capture.process_chunk("<thinking>thoughts</thinking>response")
        assert "response" in result
        assert capture.get_thinking() == "thoughts"

    def test_thinking_across_chunks(self):
        capture = ThinkingCapture()
        r1 = capture.process_chunk("Start <thin")
        r2 = capture.process_chunk("king>my thoughts</thi")
        r3 = capture.process_chunk("nking> end")
        remaining = capture.flush()

        full_response = r1 + r2 + r3 + remaining
        assert "Start" in full_response
        assert "end" in full_response
        assert "my thoughts" in capture.get_thinking()

    def test_flush_remaining(self):
        capture = ThinkingCapture()
        capture.process_chunk("hello ")
        remaining = capture.flush()
        assert capture.get_response() == "hello "

    def test_is_in_thinking_property(self):
        capture = ThinkingCapture()
        assert not capture.is_in_thinking
        capture.process_chunk("<thinking>start")
        assert capture.is_in_thinking
        capture.process_chunk("</thinking>done")
        assert not capture.is_in_thinking

    def test_reset(self):
        capture = ThinkingCapture()
        capture.process_chunk("<thinking>old</thinking>old response")
        capture.reset()
        assert capture.get_thinking() == ""
        assert capture.get_response() == ""
        assert not capture.is_in_thinking

    def test_custom_tag(self):
        capture = ThinkingCapture(tag="reflection")
        capture.process_chunk("<reflection>reflecting</reflection>answer")
        assert capture.get_thinking() == "reflecting"

    def test_empty_thinking_block(self):
        capture = ThinkingCapture()
        capture.process_chunk("<thinking></thinking>response")
        assert capture.get_response() == "response"


class TestExtractAnthropicThinking:
    def test_with_thinking_blocks(self):
        """Test with mock Anthropic response-like object."""

        class Block:
            def __init__(self, type, **kwargs):
                self.type = type
                for k, v in kwargs.items():
                    setattr(self, k, v)

        class MockResponse:
            content = [
                Block("thinking", thinking="Let me analyze this."),
                Block("text", text="The answer is 42."),
            ]

        thinking, response = extract_anthropic_thinking(MockResponse())
        assert thinking == "Let me analyze this."
        assert response == "The answer is 42."

    def test_no_thinking_blocks(self):
        class Block:
            def __init__(self, type, **kwargs):
                self.type = type
                for k, v in kwargs.items():
                    setattr(self, k, v)

        class MockResponse:
            content = [Block("text", text="Just a response.")]

        thinking, response = extract_anthropic_thinking(MockResponse())
        assert thinking == ""
        assert response == "Just a response."

    def test_empty_content(self):
        class MockResponse:
            content = []

        thinking, response = extract_anthropic_thinking(MockResponse())
        assert thinking == ""
        assert response == ""

    def test_no_content_attr(self):
        thinking, response = extract_anthropic_thinking(object())
        assert thinking == ""
        assert response == ""


class TestCreateThinkingCallback:
    def test_callback_routes_content(self):
        thinking_chunks = []
        response_chunks = []

        callback = create_thinking_callback(
            on_thinking=thinking_chunks.append,
            on_response=response_chunks.append,
        )

        callback("Hello ")
        callback("world")

        assert "Hello " in "".join(response_chunks)
        assert "world" in "".join(response_chunks)


class TestThinkingContent:
    def test_defaults(self):
        tc = ThinkingContent()
        assert tc.text == ""
        assert tc.tag_type == "thinking"
        assert tc.metadata == {}

    def test_custom_values(self):
        tc = ThinkingContent(
            text="My thoughts",
            tag_type="reflection",
            metadata={"model": "claude"},
        )
        assert tc.text == "My thoughts"
        assert tc.tag_type == "reflection"
        assert tc.metadata["model"] == "claude"
