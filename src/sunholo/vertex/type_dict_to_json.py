import typing
from typing_extensions import TypedDict, Any, Dict
    
# Type mapping for OpenAPI types to Python types
type_mapping = {
    'string': str,
    'integer': int,
    'number': float,
    'boolean': bool,
    'array': list,
    'object': dict
}

def resolve_ref(openapi_spec: Dict[str, Any], ref: str) -> Dict[str, Any]:
    """
    Resolve a $ref in the OpenAPI spec.
    
    Parameters:
    - openapi_spec: The OpenAPI specification.
    - ref: The reference string.
    
    Returns:
    - The resolved schema.
    """
    ref_path = ref.lstrip('#/').split('/')
    resolved = openapi_spec
    for part in ref_path:
        resolved = resolved.get(part)
        if resolved is None:
            raise ValueError(f"Reference {ref} could not be resolved at part {part}")
    return resolved

def openapi_to_typed_dict(openapi_spec: Dict[str, Any], schema_name: str) -> Any:
    """
    Convert an OpenAPI schema to a TypedDict dynamically.
    
    Parameters:
    - openapi_spec: The OpenAPI specification.
    - schema_name: The name of the schema to convert.
    
    Returns:
    - A dynamically created TypedDict class and field descriptions.
    """
    schema = openapi_spec['components']['schemas'][schema_name]
    properties = schema['properties']
    required = schema.get('required', [])
    annotations = {}
    descriptions = {}

    def process_property(key: str, value: Dict[str, Any]) -> Any:
        """Process an individual property and update annotations and descriptions."""
        if '$ref' in value:
            value = resolve_ref(openapi_spec, value['$ref'])
        
        field_type = value.get('type')
        if field_type in type_mapping:
            annotations[key] = type_mapping[field_type]
        elif field_type == 'array':
            item_ref = value['items'].get('$ref')
            item_type = value['items'].get('type')
            if item_ref:
                item_schema = resolve_ref(openapi_spec, item_ref)
                item_typed_dict, _ = openapi_to_typed_dict(openapi_spec, item_schema['title'])
                annotations[key] = typing.List[item_typed_dict]
            elif item_type in type_mapping:
                annotations[key] = typing.List[type_mapping[item_type]]
            else:
                annotations[key] = typing.List[dict]
        elif field_type == 'object':
            annotations[key] = dict
            nested_properties = value.get('properties', {})
            nested_required = value.get('required', [])
            nested_annotations = {}
            for nested_key, nested_value in nested_properties.items():
                nested_annotations[nested_key] = process_property(nested_key, nested_value)
            annotations[key] = TypedDict(f"{key.capitalize()}Nested", nested_annotations, total=False)
            for nested_key in nested_required:
                annotations[key].__annotations__[nested_key] = nested_annotations[nested_key]
        
        descriptions[key] = value.get('description', '')
        return annotations[key]

    for key, value in properties.items():
        process_property(key, value)

    typed_dict_cls = TypedDict(schema_name, annotations, total=False)
    for key in required:
        typed_dict_cls.__annotations__[key] = annotations[key]

    return typed_dict_cls, descriptions

def describe_typed_dict(typed_dict_cls: Any, descriptions: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate a dictionary with field descriptions.
    
    Parameters:
    - typed_dict_cls: The TypedDict class.
    - descriptions: The dictionary containing field descriptions.
    
    Returns:
    - A dictionary with field descriptions.
    """
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    for key, value in typed_dict_cls.__annotations__.items():
        description = descriptions.get(key, "")
        property_schema = {
            "type": value.__name__.lower() if isinstance(value, type) else "object",
            "description": description
        }
        if typing.get_origin(value) is list:
            item_type = typing.get_args(value)[0]
            property_schema["items"] = {"type": item_type.__name__.lower()}
        elif typing.get_origin(value) is dict:
            property_schema["properties"] = describe_typed_dict(value, descriptions)["properties"]
        schema["properties"][key] = property_schema
        if key in typed_dict_cls.__required_keys__:
            schema["required"].append(key)
    return schema


def is_typed_dict(cls):
    """Check if a class is a TypedDict."""
    return isinstance(cls, type) and issubclass(cls, dict) and hasattr(cls, '__annotations__')
