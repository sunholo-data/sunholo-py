import os

def has_multivac_api_key():
    if os.getenv('MULTIVAC_API_KEY'):
        return True
    
    return False

def get_multivac_api_key():
    if has_multivac_api_key():
        return os.getenv('MULTIVAC_API_KEY')
    
    return None