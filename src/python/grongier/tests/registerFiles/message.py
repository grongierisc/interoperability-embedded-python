from grongier.pex import Message

from dataclasses import dataclass

from obj import PostClass

@dataclass
class PostMessage(Message):

    Post:PostClass = None
    ToEmailAddress:str = None
    Found:str = None

@dataclass
class MyResponse(Message):
    value:str = None