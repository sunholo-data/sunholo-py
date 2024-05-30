import uuid
import hashlib
import platform
import socket

def generate_user_id():
    data = f"{socket.gethostname()}-{platform.platform()}-{platform.processor()}"
    hashed_id = hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hashed_id))
