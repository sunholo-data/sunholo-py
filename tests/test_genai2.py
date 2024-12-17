from sunholo.genai import GoogleAI, GoogleAIConfig
from typing import Optional, List, Union, Dict, Any, TypedDict
import enum
from pydantic import BaseModel

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
    #response = ai.generate_text(
    #    "Write a short poem about AI",
    #    temperature=0.8
    #)
    #print(response)
    
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

    # google search
    google_tool = ai.google_search_tool()
    response = ai.generate_text(
        "What is the news today in Denmark?",
        tools=[google_tool],
        temperature=0.8
    )
    print(response)

    # define own functions
    def get_current_weather(location: str,) -> int:
        """Returns the current weather.

        Args:
            location: The city and state, e.g. San Francisco, CA
        """
        return 'sunny'

    response = ai.generate_text(
        "What is the weather today in Copenhagen?",
        tools=[get_current_weather],
        temperature=0.8
    )
    print(response)

    # both not allowed
    try:
        response = ai.generate_text(
            "What is the weather today in Copenhagen, and can you search for activities good for that weather?",
            tools=[get_current_weather, google_tool],
            temperature=0.8
        )
        print(response)
    except Exception as err:
        print(err)
    
    # images
    an_image = ai.local_file("/Users/mark/dev/sunholo/sunholo-py/docs/static/img/eclipse1.png")
    response = ai.generate_text(
        ["Describe this image", an_image],
    )
    print(response)

    # upload file

    ## download first example
    import requests
    import pathlib
    gs_uri = "https://storage.googleapis.com/sunholo-public-podcasts/emissary-person.png"
    file_bytes = requests.get(gs_uri).content
    file_path = pathlib.Path('person.png')
    file_path.write_bytes(file_bytes)

    # upload image to genai client
    file_upload = ai.client.files.upload(path=file_path)
    an_image = ai.gs_uri(file_upload.uri)
    response = ai.generate_text(
        ["Describe this image", an_image],
    )
    print(response)