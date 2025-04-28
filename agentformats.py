from pydantic import BaseModel, Field
from typing import Type, List, Tuple, Optional

def _get_format_metadata(format: Type[BaseModel]|None=None) -> dict:
    """ Genera i metadati per il formato specificato. """
    return {
        "type": "json_schema",
        "json_schema": {
            "schema": format.model_json_schema(),
            "strict": True
        }
    } if format else {}


# *********************
# Exemplary classes ***
# *********************

class DecimalNumber(BaseModel):
    """ A decimal number."""
    number: float = Field(..., description="A decimal number.")
    rounding: Optional[int] = Field(2, description="The number of digits to which the given number must be rounded.")

class List_(BaseModel):
    """ A list of entities, as strings."""
    list: List[str] = Field(..., description="A list of entities, where each entity is a string.")

'''
class ActionList:
    """ A list of pairs of strings (agent name, request)."""
    list: List[Tuple[str, str]] = field(default_factory=list, metadata={
        "description": "A list of pairs of strings (agent name, request)." 
    })

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
'''

#import json
#print(json.dumps(list_schema, indent=2))