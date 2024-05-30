VAC_SUBCONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "llm": {"type": "string"},
        "agent": {"type": "string"},
        "model": {"type": "string"},
        "prompt": {"type": "string"},
        "chunker": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "llm": {"type": "string"},
                "chunk_size": {"type": "integer"},
                "overlap": {"type": "integer"},
                "summarise": {
                    "type": "object",
                    "properties": {
                        "llm": {"type": "string"},
                        "model": {"type": "string"},
                        "threshold": {"type": "integer"},
                        "model_limit": {"type": "integer"}
                    }
                    },
            },
            "additionalProperties": False
        },
        "memory": {
            "type": "array",
            "items": {
                "type": "object",
                "patternProperties": {
                    ".*-vectorstore": {
                        "type": "object",
                        "properties": {
                            "vectorstore": {"type": "string"},
                            "self_query": {"type": "boolean"},
                            "provider": {"type": "string"},
                            "k": {"type": "integer"},
                            "vector_name": {"type": "string"},
                            "read_only": {"type": "boolean"},
                            "llm": {"type": "string"}
                        },
                        "required": ["vectorstore"]
                    }
                }
            }
        },
        "gcp_config": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "endpoint_id": {"type": "integer"},
                "location": {"type": "string"}
            }
        },
        "alloydb_config": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "region": {"type": "string"},
                "cluster": {"type": "string"},
                "instance": {"type": "string"},
                "database": {"type": "string"}
            },
            "required": ["project_id", "region", "cluster", "instance"]
        },
        "secrets": {
            "type": "array",
            "items": {"type": "string"}
        },
        "display_name": {"type": "string"},
        "avatar_url": {"type": "string"},
        "description": {"type": "string"},
        "memory_k": {"type": "integer"}
    },
    "required": ["llm", "agent"]
}


VAC_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string"},
        "apiVersion": {"type": "string"},
        "gcp_config": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "location": {"type": "string"}
            },
            "required": ["project_id", "location"]
        },
        "vac": {
            "type": "object",
            "patternProperties": {
                ".*": VAC_SUBCONFIG_SCHEMA
            }
        }
    },
    "required": ["kind", "apiVersion", "vac"]
}

PROMPT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string"},
        "apiVersion": {"type": "string"},
        "prompts": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "chunk_summary": {"type": "string"},
                        "intro": {"type": "string"},
                        "template": {"type": "string"},
                        "chat_summary": {"type": "string"},
                        "summarise_known_question": {"type": "string"}
                    }
                }
            }
        }
    },
    "required": ["kind", "apiVersion", "prompts"]
}

SCHEMAS = {
    "vacConfig": VAC_CONFIG_SCHEMA,
    "promptConfig": PROMPT_CONFIG_SCHEMA
}

