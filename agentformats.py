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
    numero: float = Field(..., description="A decimal number.")
    arrotondamento: Optional[int] = Field(2, description="The number of digits to which the given number must be rounded.")

class Elenco(BaseModel):
    """ Un elenco di entità, come stringhe."""
    elenco: List[str] = Field(..., description="Un elenco di entità, in cui ogni entità è una stringa.")

class RagionamentoPassoPasso(BaseModel):
    """ La struttura di un ragionamento che giunge alla conclusione passo per passo,
    spiegando ogni passaggio in dettaglio, senza accontentarsi della prima ipotesi formulata,
    e solo dopo aver controllato la correttezza di tutti i passaggi."""
    passi_del_ragionamento: List[str] = Field(..., description="L'elenco dei passi del ragionamento per giungere alla conclusione del problema dato.")
    conclusione: str = Field(..., description="La conclusione del problema dato.")


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