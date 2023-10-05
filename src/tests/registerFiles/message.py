from typing import List, Dict
from grongier.pex import Message, PickleMessage

from dataclasses import dataclass

from obj import PostClass

from datetime import datetime, date, time

@dataclass
class FullMessage(Message):

    embedded:PostClass
    embedded_list:List[PostClass]
    embedded_dict:Dict[str,PostClass]
    string:str
    integer:int
    float:float
    boolean:bool
    list:List
    dict:Dict
    list_dict:List[dict]
    dict_list:Dict[str,List]
    date:date
    datetime:datetime
    time:time



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