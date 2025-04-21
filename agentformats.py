from dataclasses import dataclass, field
from typing import List, Optional
from agents import dataclass_to_openai_schema

@dataclass
class DecimalNumber:
    """ Un numero decimale."""
    number: float = field(metadata={"description": "Un numero decimale"})
    rounding: Optional[int] = field(metadata={"description": "Il numero di cifre decimali a cui arrotondare il numero dato."})

decimal_number_schema = dataclass_to_openai_schema(DecimalNumber)

@dataclass
class Elenco:
    """ Un elenco di entità, indicate come stringhe."""
    elenco: List[str] = field(default_factory=list, metadata={
        "description": "Un elenco di entità, ognuna nella forma di una stringa" ,
        "uniqueItems": True
    })

list_schema = dataclass_to_openai_schema(Elenco)

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