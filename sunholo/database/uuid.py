import uuid

def generate_uuid_from_object_id(object_id):
    # UUID namespace for example purposes; in a real application, you might choose a fixed namespace
    namespace = uuid.NAMESPACE_URL
    return uuid.uuid5(namespace, object_id)