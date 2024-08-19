import os

def init_genai():
    """
    There are some features that come to the google.generativeai first, 
    which needs to be authenticated via a GOOGLE_API_KEY environment variable, 
    created via the Google AI Console at https://aistudio.google.com/app/apikey 
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("google.generativeai not installed, please install via 'pip install sunholo'[gcp]'")
    
    GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("google.generativeai needs GOOGLE_API_KEY set in environment variable")

    genai.configure(api_key=GOOGLE_API_KEY)