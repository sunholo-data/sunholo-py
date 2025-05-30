

def convert_composite_to_native(value):
    """
    Recursively converts a proto MapComposite or RepeatedComposite object to native Python types.

    Args:
        value: The proto object, which could be a MapComposite, RepeatedComposite, or a primitive.

    Returns:
        The equivalent Python dictionary, list, or primitive type.
    """
    import proto
    
    if isinstance(value, proto.marshal.collections.maps.MapComposite):
        # Convert MapComposite to a dictionary, recursively processing its values
        return {key: convert_composite_to_native(val) for key, val in value.items()}
    elif isinstance(value, proto.marshal.collections.repeated.RepeatedComposite):
        # Convert RepeatedComposite to a list, recursively processing its elements
        return [convert_composite_to_native(item) for item in value]
    else:
        # If it's a primitive value, return it as is
        return value


