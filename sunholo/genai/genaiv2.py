from typing import Optional, List, Union, Dict, Any, TypedDict, TYPE_CHECKING, Generator

import enum
import json
from pydantic import BaseModel
import time
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    import sounddevice as sd
except ImportError:
    sd = None
except OSError:
    sd = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import cv2 as cv2
except ImportError:
    cv2 = None

if TYPE_CHECKING:
    from google import genai
    from google.genai import types
    from google.genai.types import Tool, GenerateContentConfig, EmbedContentConfig
else:
    genai = None

class GoogleAIConfig(BaseModel):
    """Configuration class for GoogleAI client initialization.
    See https://ai.google.dev/gemini-api/docs/models/gemini-v2
    """
    api_key: Optional[str] = None
    project_id: Optional[str] = None
    location: str = "us-central1"
    use_vertex: bool = False

class GoogleAI:
    """A wrapper class for Google's v2 Generative AI APIs.
    See https://ai.google.dev/gemini-api/docs/models/gemini-v2
    """
    
    def __init__(self, config: GoogleAIConfig):
        """Initialize the GoogleAI client.
        
        Args:
            config (GoogleAIConfig): Configuration for client initialization
        """
        if genai is None:
            raise ImportError("GoogleAI requires google-genai to be installed, try sunholo[gcp]")
        if config.use_vertex:
            if not config.project_id:
                raise ValueError("project_id is required for Vertex AI")
            self.client = genai.Client(
                vertexai=True,
                project=config.project_id,
                location=config.location
            )
        else:
            if not config.api_key:
                raise ValueError("api_key is required for Google AI API")
            self.client = genai.Client(api_key=config.api_key)
        
        self.default_model = "gemini-2.0-flash-exp"
    
    def google_search_tool(self) -> "types.Tool":
        from google.genai.types import Tool, GoogleSearch
        return Tool(
            google_search = GoogleSearch()
        )
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 20,
        stop_sequences: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List["types.Tool"]] = None
    ) -> str:
        """Generate text using the specified model.
        
        Args:
            prompt (str): The input prompt
            model (Optional[str]): Model name to use
            temperature (float): Controls randomness (0.0-1.0)
            max_output_tokens (int): Maximum number of tokens to generate
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-k sampling parameter
            stop_sequences (Optional[List[str]]): Sequences that stop generation
            system_prompt (Optional[str]): System-level instruction
            tools: list of python functions or Tool objects
            
        Returns:
            str: Generated text response
        """
        model = model or self.default_model
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences or [],
            tools=tools or []
        )
        
        if system_prompt:
            config.system_instruction = system_prompt
            
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        return response.text

    async def generate_text_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Async version of generate_text."""
        model = model or self.default_model
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**kwargs)
        )
        return response.text
        
    async def _record_audio(
            self,
            duration: float = 5.0,
            sample_rate: int = 16000
        ) -> bytes:
        """Internal method to record audio."""
        if sd is None or np is None:
            raise ImportError("sounddevice and numpy are required for audio. Install with pip install sunholo[tts]")
        
        print(f"Recording for {duration} seconds...")
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
        print("Recording complete")
        return audio_data.tobytes()

    async def _record_video(
            self,
            duration: float = 5.0
        ) -> List[bytes]:
        """Internal method to record video frames."""
        import cv2
        
        frames = []
        screen = cv2.VideoCapture(0)
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                ret, frame = screen.read()
                if ret:
                    _, buffer = cv2.imencode('.jpg', frame)
                    frames.append(buffer.tobytes())
                    time.sleep(0.1)  # Limit frame rate
        finally:
            screen.release()
        
        return frames

    async def _process_responses(self, session) -> List[str]:
        """Internal method to process session responses."""
        responses = []
        i = 1
        async for response in session.receive():
            model_turn = response.server_content.model_turn
            if model_turn is None:
                continue
            for part in model_turn.parts:
                text = part.text
                print(f"[{i}] {text}")
                i += 1
                responses.append(text)
        return responses

    async def live_async(
            self,
            prompt: Optional[Union[str, List[Union[str, bytes]]]] = None,
            input_type: str = "text",  # "text", "audio", or "video"
            duration: Optional[float] = None,  # For audio/video recording duration
            model: Optional[str] = None,
            **kwargs
        ) -> str:
        """Live Multimodal API with support for text, audio, and video inputs.
        
        Args:
            input_type: Type of input ("text", "audio", or "video")
            prompt: Text prompt or list of text/binary chunks
            duration: Recording duration for audio/video in seconds
            model: Optional model name
            **kwargs: Additional configuration parameters
        
        Returns:
            str: Generated response text
        """
        client = genai.Client(
            http_options={
                'api_version': 'v1alpha',
                'url': 'generativelanguage.googleapis.com',
            }
        )
        
        config = {
            "generation_config": {"response_modalities": ["TEXT"]}
        }

        async with client.aio.live.connect(model=self.default_model, config=config) as session:
            # Handle different input types
            if input_type == "text":
                message = {
                    "client_content": {
                        "turns": [
                            {
                                "parts": [{"text": prompt}],
                                "role": "user"
                            }
                        ],
                        "turn_complete": True
                    }
                }
                await session.send(json.dumps(message), end_of_turn=True)
            
            elif input_type == "audio":
                audio_data = await self._record_audio(duration=duration or 5.0)
                message = {"media_chunks": [audio_data]}
                await session.send(message)
                await session.send(json.dumps({"turn_complete": True}), end_of_turn=True)
            
            elif input_type == "video":
                frames = await self._record_video(duration=duration or 5.0)
                for frame in frames:
                    message = {"media_chunks": [frame]}
                    await session.send(message)
                await session.send(json.dumps({"turn_complete": True}), end_of_turn=True)
            
            else:
                raise ValueError(f"Unsupported input_type: {input_type}")

            # Process responses
            responses = await self._process_responses(session)
            return "OK"
        
    def gs_uri(self, uri, mime_type=None):
      
        if mime_type is None:
            from ..utils.mime import guess_mime_type
            mime_type = guess_mime_type(uri)

        return types.Part.from_uri(
            file_uri=uri,
            mime_type=mime_type,
        )

    def local_file(self, filename, mime_type=None):
        if mime_type is None:
            from ..utils.mime import guess_mime_type
            mime_type = guess_mime_type(filename)

        with open(filename, 'rb') as f:
            image_bytes = f.read()
        
        if image_bytes and mime_type:
            return types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
        else:
            raise ValueError(f"Could not read bytes or mime_type for {filename=} - {mime_type=}")

    def stream_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> "Generator[str, None, None]":
        """Stream text generation responses.
        
        Args:
            prompt (str): The input prompt
            model (Optional[str]): Model name to use
            **kwargs: Additional configuration parameters
            
        Yields:
            str: Chunks of generated text
        """
        model = model or self.default_model
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**kwargs)
        ):
            yield chunk.text
            
    def get_embedding(
        self,
        text: Union[str, List[str]],
        model: str = "text-embedding-004",
        output_dim: Optional[int] = None
    ) -> Union[List[float], List[List[float]]]:
        """Get text embeddings.
        
        Args:
            text (Union[str, List[str]]): Text to embed
            model (str): Embedding model to use
            output_dim (Optional[int]): Desired embedding dimension
            
        Returns:
            Union[List[float], List[List[float]]]: Embeddings
        """
        config = {}
        if output_dim:
            config["output_dimensionality"] = output_dim
            
        response = self.client.models.embed_content(
            model=model,
            contents=text,
            config=types.EmbedContentConfig(**config) if config else None
        )
        
        if isinstance(text, str):
            return response.embeddings[0].values
        return [emb.values for emb in response.embeddings]

    def structured_output(
        self,
        prompt: str,
        schema: Union[BaseModel, Dict, type, TypedDict],
        model: Optional[str] = None,
        is_list: bool = False
    ) -> Dict:
        """Generate structured output according to a schema.
        
        Args:
            prompt (str): Input prompt
            schema (Union[BaseModel, Dict, type]): Schema definition (Pydantic model, TypedDict, or raw schema)
            model (Optional[str]): Model to use
            is_list (bool): Whether to wrap the schema in a list
            
        Returns:
            Dict: Structured response matching schema
        """
        model = model or self.default_model
        
        # Handle TypedDict differently than Pydantic models
        if isinstance(schema, type):
            if hasattr(schema, '__origin__') and schema.__origin__ is list:
                # Handle list[TypedDict] case
                inner_type = schema.__args__[0]
                config = types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=schema
                )
            elif hasattr(schema, '__annotations__'):  # TypedDict check
                # Create API-compatible schema
                schema_dict = {
                    'type': 'OBJECT',
                    'properties': {},
                    'required': list(schema.__annotations__.keys())  # TypedDict fields are required by default
                }
                
                for field_name, field_type in schema.__annotations__.items():
                    if hasattr(field_type, '__base__') and field_type.__base__ == enum.Enum:
                        schema_dict['properties'][field_name] = {
                            'type': 'STRING',
                            'enum': [e.value for e in field_type]
                        }
                    elif field_type is str:
                        schema_dict['properties'][field_name] = {'type': 'STRING'}
                    elif field_type is int:
                        schema_dict['properties'][field_name] = {'type': 'INTEGER'}
                    elif field_type is float:
                        schema_dict['properties'][field_name] = {'type': 'NUMBER'}
                    elif field_type is bool:
                        schema_dict['properties'][field_name] = {'type': 'BOOLEAN'}
                    else:
                        schema_dict['properties'][field_name] = {'type': 'STRING'}
                
                if is_list:
                    schema_dict = {
                        'type': 'ARRAY',
                        'items': schema_dict
                    }
                
                config = types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=schema_dict
                )
            elif hasattr(schema, '__origin__') and schema.__origin__ is list:
                # Handle List[TypeDict] case
                inner_type = schema.__args__[0]
                if hasattr(inner_type, '__annotations__'):  # Check if inner type is TypedDict
                    # Create API-compatible schema for the inner TypedDict
                    schema_dict = {
                        'type': 'OBJECT',
                        'properties': {},
                        'required': list(inner_type.__annotations__.keys())
                    }
                    
                    for field_name, field_type in inner_type.__annotations__.items():
                        if hasattr(field_type, '__base__') and field_type.__base__ == enum.Enum:
                            schema_dict['properties'][field_name] = {
                                'type': 'STRING',
                                'enum': [e.value for e in field_type]
                            }
                        elif field_type is str:
                            schema_dict['properties'][field_name] = {'type': 'STRING'}
                        elif field_type is int:
                            schema_dict['properties'][field_name] = {'type': 'INTEGER'}
                        elif field_type is float:
                            schema_dict['properties'][field_name] = {'type': 'NUMBER'}
                        elif field_type is bool:
                            schema_dict['properties'][field_name] = {'type': 'BOOLEAN'}
                        else:
                            schema_dict['properties'][field_name] = {'type': 'STRING'}
                    
                    # Wrap in array type
                    array_schema = {
                        'type': 'ARRAY',
                        'items': schema_dict
                    }
                    
                    config = types.GenerateContentConfig(
                        response_mime_type='application/json',
                        response_schema=array_schema
                    )
            elif issubclass(schema, BaseModel):
                # Convert Pydantic model to Google's schema format
                schema_dict = {
                    'type': 'OBJECT',
                    'properties': {},
                    'required': []
                }
                
                for field_name, field_info in schema.model_fields.items():
                    # Handle different field types including enums
                    if isinstance(field_info.annotation, type) and issubclass(field_info.annotation, enum.Enum):
                        field_type = {
                            'type': 'STRING',
                            'enum': [e.value for e in field_info.annotation]
                        }
                    elif field_info.annotation is str:
                        field_type = {'type': 'STRING'}
                    elif field_info.annotation is int:
                        field_type = {'type': 'INTEGER'}
                    elif field_info.annotation is float:
                        field_type = {'type': 'NUMBER'}
                    elif field_info.annotation is bool:
                        field_type = {'type': 'BOOLEAN'}
                    elif field_info.annotation is list or (
                        hasattr(field_info.annotation, '__origin__') and 
                        field_info.annotation.__origin__ is list
                    ):
                        # Handle typed lists
                        if hasattr(field_info.annotation, '__args__'):
                            inner_type = field_info.annotation.__args__[0]
                            if inner_type is str:
                                item_type = 'STRING'
                            elif inner_type is int:
                                item_type = 'INTEGER'
                            elif inner_type is float:
                                item_type = 'NUMBER'
                            elif inner_type is bool:
                                item_type = 'BOOLEAN'
                            else:
                                item_type = 'STRING'
                        else:
                            item_type = 'STRING'
                        field_type = {'type': 'ARRAY', 'items': {'type': item_type}}
                    else:
                        field_type = {'type': 'STRING'}
                    
                    schema_dict['properties'][field_name] = field_type
                    if field_info.is_required:
                        schema_dict['required'].append(field_name)
                
                if is_list:
                    schema_dict = {
                        'type': 'ARRAY',
                        'items': schema_dict
                    }
                
                config = types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=schema_dict
                )
        else:
            # Handle raw schema dict
            config = types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=schema
            )
            
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        return response.text
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count the number of tokens in the text.
        
        Args:
            text (str): Input text
            model (Optional[str]): Model to use for tokenization
            
        Returns:
            int: Number of tokens
        """
        model = model or self.default_model
        response = self.client.models.count_tokens(
            model=model,
            contents=text
        )
        return response.total_tokens

