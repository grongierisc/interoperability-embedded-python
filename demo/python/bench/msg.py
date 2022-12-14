from grongier.pex import Message
from grongier.pex import PickleMessage
from dataclasses import dataclass

@dataclass
class MyBench(Message):
    property_name_0:str = None
    property_name_1:str = None
    property_name_2:str = None
    property_name_3:str = None
    property_name_4:str = None
    property_name_5:str = None
    property_name_6:str = None
    property_name_7:str = None
    property_name_8:str = None
    property_name_9:str = None

@dataclass
class MyBenchPickle(PickleMessage):
    property_name_0:str = None
    property_name_1:str = None
    property_name_2:str = None
    property_name_3:str = None
    property_name_4:str = None
    property_name_5:str = None
    property_name_6:str = None
    property_name_7:str = None
    property_name_8:str = None
    property_name_9:str = None