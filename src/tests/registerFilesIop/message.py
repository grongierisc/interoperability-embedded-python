from typing import List, Dict
from iop import Message, PickleMessage

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
    list_dict:List[Dict]
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
class ComplexMessage(Message):
    post:PostClass = None
    string:str = None
    list_str:List[str] = None
    list_int:List[int] = None
    list_post:List[PostClass] = None
    dict_str:Dict[str,str] = None
    dict_int:Dict[str,int] = None
    dict_post:Dict[str,PostClass] = None    

@dataclass
class MyResponse(Message):
    value:str = None

@dataclass
class SimpleMessage(Message):
    integer : int 
    string : str

class SimpleMessageNotDataclass(Message):
    integer : int 
    string : str

class SimpleMessageNotMessage:
    integer : int 
    string : str

@dataclass
class PickledMessage(PickleMessage):
    integer : int 
    string : str