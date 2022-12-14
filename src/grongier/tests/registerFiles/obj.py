from dataclasses import dataclass, field

@dataclass
class PostClass:
    Title: str
    Selftext : str
    Author: str
    Url: str
    CreatedUTC: float = None
    OriginalJSON: str = None