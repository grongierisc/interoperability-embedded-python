from dataclasses import dataclass, field
from dataclasses_json import LetterCase, dataclass_json, config

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class PostClass:
    Title: str
    Selftext : str
    Author: str
    Url: str
    CreatedUTC: float = field(metadata=config(field_name="created_utc"))
    OriginalJSON: str = None