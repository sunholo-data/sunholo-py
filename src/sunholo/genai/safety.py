
def genai_safety(threshold: str = "BLOCK_ONLY_HIGH"):
    """
    BLOCK_ONLY_HIGH - block when high probability of unsafe content is detected
    BLOCK_MEDIUM_AND_ABOVE - block when medium or high probability of content is detected
    BLOCK_LOW_AND_ABOVE - block when low, medium, or high probability of unsafe content is detected
    BLOCK_NONE - no block, but need to be on an allow list to use
    """
    from google.generativeai.types import (
        HarmCategory,
        HarmBlockThreshold
    )

    if threshold == 'BLOCK_ONLY_HIGH':
        thresh = HarmBlockThreshold.BLOCK_ONLY_HIGH
    elif threshold == 'BLOCK_MEDIUM_AND_ABOVE':
        thresh = HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    elif threshold == 'BLOCK_LOW_AND_ABOVE':
        thresh = HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
    elif threshold == 'BLOCK_NONE':
        thresh = HarmBlockThreshold.BLOCK_NONE
    else:
        raise ValueError("Invalid threshold")

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: thresh,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: thresh,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: thresh,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: thresh,
    }

    return safety_settings