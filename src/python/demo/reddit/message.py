from grongier.pex import Message

from dataclasses import dataclass

from obj import PostClass

@dataclass
class PostMessage(Message):

    Post:PostClass = None
    ToEmailAddress:str = None
    Found:str = None

@dataclass
class MyRequest(Message):

    maString:str = None

@dataclass
class MyMessage(Message):
    toto:str = None