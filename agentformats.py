from dataclasses import dataclass, field, fields, is_dataclass
from typing import get_type_hints, Union, get_args, get_origin, List, Tuple, Optional

# **************************************************************************
# Functions to parse dataclasses and create OpenAI formatted output JSON ***
# **************************************************************************

def is_optional_type(t):
    return get_origin(t) is Union and type(None) in get_args(t)

def unwrap_optional(t):
    if is_optional_type(t):
        return [arg for arg in get_args(t) if arg is not type(None)][0]
    return t

"""    
def python_type_to_openai(t, metadata=None):
    origin = get_origin(t)
    args = get_args(t)
    metadata = metadata or {}

    if is_optional_type(t):
        return python_type_to_openai(unwrap_optional(t), metadata)

    if origin in (list, List):
        item_type = args[0] if args else str
        schema = {
            "type": "array",
            "items": {
                "type": python_type_to_openai(item_type)
            }
        }
        for key in ["minItems", "maxItems", "uniqueItems"]:
            if key in metadata:
                schema[key] = metadata[key]
        return schema

    if t is str:
        return "string"
    elif t is int:
        return "integer"
    elif t is float:
        return "number"
    elif t is bool:
        return "boolean"
    elif is_dataclass(t):
        return dataclass_to_openai_schema(t)
    else:
        return "string"
"""

def python_type_to_openai(t, metadata=None):
    origin = get_origin(t)
    args = get_args(t)
    metadata = metadata or {}

    if is_optional_type(t):
        return python_type_to_openai(unwrap_optional(t), metadata)

    if origin in (list, List):
        item_type = args[0] if args else str

        # Handle List[Tuple[...]]
        if get_origin(item_type) in (tuple, Tuple):
            tuple_args = get_args(item_type)
            return {
                "type": "array",
                "items": {
                    "type": "array",
                    "prefixItems": [ 
                        {"type": python_type_to_openai(arg)} if isinstance(python_type_to_openai(arg), str) 
                        else python_type_to_openai(arg)
                        for arg in tuple_args
                    ],
                    "minItems": len(tuple_args),
                    "maxItems": len(tuple_args)
                },
                "description": metadata.get("description", "")
            }

        # Regular list
        schema = {
            "type": "array",
            "items": {
                "type": python_type_to_openai(item_type)
            }
        }
        for key in ["minItems", "maxItems", "uniqueItems"]:
            if key in metadata:
                schema[key] = metadata[key]
        return schema

    if t is str:
        return "string"
    elif t is int:
        return "integer"
    elif t is float:
        return "number"
    elif t is bool:
        return "boolean"
    elif is_dataclass(t):
        return dataclass_to_openai_schema(t)
    else:
        return "string"


def dataclass_to_openai_schema(cls):
    props = {}
    required = []

    type_hints = get_type_hints(cls)

    for f in fields(cls):
        field_type = type_hints.get(f.name, str)
        description = f.metadata.get("description", "")
        json_type = python_type_to_openai(field_type, f.metadata)

        if isinstance(json_type, str):
            prop = {"type": json_type}
        else:
            prop = json_type

        if description:
            prop["description"] = description

        props[f.name] = prop

        # Only required if not Optional
        if not is_optional_type(field_type):
            required.append(f.name)

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "agent_response",
            "description": "Response from the agent",
            "strict": "true",
            "schema": {
                "type": "object",
                "properties": props,
                "required": required,
            }
        }
    }

    return schema



# ********************************************************
# Example dataclasses to be converted to OpenAI schema ***
# ********************************************************

@dataclass
class DecimalNumber:
    """ A decimal number."""
    number: float = field(metadata={"description": "A decimal number."})
    rounding: Optional[int] = field(metadata={"description": "The number of digits to which the given number must be rounded."})

decimal_number_schema = dataclass_to_openai_schema(DecimalNumber)


@dataclass
class List_:
    """ A list of entities, as strings."""
    list: List[str] = field(default_factory=list, metadata={
        "description": "A list of entities, where each is a string." 
    })

list_schema = dataclass_to_openai_schema(List_)


@dataclass
class ActionList:
    """ A list of pairs of strings (agent name, request)."""
    list: List[Tuple[str, str]] = field(default_factory=list, metadata={
        "description": "A list of pairs of strings (agent name, request)." 
    })

action_list_schema = dataclass_to_openai_schema(ActionList)


@dataclass
class User:
    """
    Represents a user of the system.
    """
    name: str = field(metadata={"description": "The full name of the user."})
    age: int = field(metadata={"description": "The age of the user in years."})
    email: Optional[str] = field(metadata={"description": "The user's email address."})
    hobbies: List[str] = field(default_factory=list, metadata={
        "description": "A list of the user's hobbies." ,
        "minItems": 1,
        "maxItems": 5,
        "uniqueItems": True
    })

user_schema = dataclass_to_openai_schema(User)





#import json
#print(json.dumps(list_schema, indent=2))

# an example
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "risposta",
        "strict": "true",
        "schema": {
            "type": "object",
            "properties": {
                "nazioni": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "Nome di una nazione europea"
                    },
                    "minItems": 5,
                    "maxItems": 5,
                    "uniqueItems": True,
                    "description": "Un elenco di nazioni europee",
                }
            },
            "required": ["nazioni"]
        }
    }
}