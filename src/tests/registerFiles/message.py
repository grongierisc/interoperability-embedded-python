from grongier.pex import Message, PickleMessage

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

@dataclass
class TestSimpleMessage(Message):
    integer : int 
    string : str

class TestSimpleMessageNotDataclass(Message):
    integer : int 
    string : str

class TestSimpleMessageNotMessage:
    integer : int 
    string : str

@dataclass
class TestPickledMessage(PickleMessage):
    integer : int 
    string : str