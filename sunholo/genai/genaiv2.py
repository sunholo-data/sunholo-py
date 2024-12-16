from typing import Optional, List, Union, Dict, Any, TypedDict
import enum
from pydantic import BaseModel
try:
    from google import genai
    from google.genai import types
except ImportError:
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
    
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 20,
        stop_sequences: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
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

    def stream_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ):
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
                    elif field_type == str:
                        schema_dict['properties'][field_name] = {'type': 'STRING'}
                    elif field_type == int:
                        schema_dict['properties'][field_name] = {'type': 'INTEGER'}
                    elif field_type == float:
                        schema_dict['properties'][field_name] = {'type': 'NUMBER'}
                    elif field_type == bool:
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
                        elif field_type == str:
                            schema_dict['properties'][field_name] = {'type': 'STRING'}
                        elif field_type == int:
                            schema_dict['properties'][field_name] = {'type': 'INTEGER'}
                        elif field_type == float:
                            schema_dict['properties'][field_name] = {'type': 'NUMBER'}
                        elif field_type == bool:
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
                    elif field_info.annotation == str:
                        field_type = {'type': 'STRING'}
                    elif field_info.annotation == int:
                        field_type = {'type': 'INTEGER'}
                    elif field_info.annotation == float:
                        field_type = {'type': 'NUMBER'}
                    elif field_info.annotation == bool:
                        field_type = {'type': 'BOOLEAN'}
                    elif field_info.annotation == list or (
                        hasattr(field_info.annotation, '__origin__') and 
                        field_info.annotation.__origin__ == list
                    ):
                        # Handle typed lists
                        if hasattr(field_info.annotation, '__args__'):
                            inner_type = field_info.annotation.__args__[0]
                            if inner_type == str:
                                item_type = 'STRING'
                            elif inner_type == int:
                                item_type = 'INTEGER'
                            elif inner_type == float:
                                item_type = 'NUMBER'
                            elif inner_type == bool:
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

# Example usage:
if __name__ == "__main__":
    import os
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("Need to set GOOGLE_API_KEY environment variable")
    
    # Initialize with Google AI API
    config = GoogleAIConfig(
        api_key=os.getenv("GOOGLE_API_KEY"),
    )
    ai = GoogleAI(config)
    
    # Basic text generation
    response = ai.generate_text(
        "Write a short poem about AI",
        temperature=0.8
    )
    print(response)
    
    # Structured output example
    from pydantic import BaseModel
    
    class MovieReview(BaseModel):
        title: str
        rating: float
        tags: List[str]
        summary: str
        
    review = ai.structured_output(
        "Review the movie 'Inception'",
        MovieReview
    )
    print(review)
    
    # Streaming example
    #for chunk in ai.stream_text("Tell me a story"):
    #    print(chunk, end="")

    import enum
    from typing_extensions import TypedDict

    class Grade(enum.Enum):
        A_PLUS = "a+"
        A = "a"
        B = "b"
        C = "c"
        D = "d"
        F = "f"

    class Recipe(TypedDict):
        recipe_name: str
        grade: Grade
    
    enum_review = ai.structured_output(
        "List about 10 cookie recipes, grade them based on popularity",
        Recipe, 
        is_list=True
    )
    print(enum_review)