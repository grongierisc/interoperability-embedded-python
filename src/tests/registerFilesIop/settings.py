import bp
from bo import *
from bs import RedditService
from message import SimpleMessage, PostMessage

SCHEMAS = [SimpleMessage, PostMessage]

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.FileOperation': FileOperation,
    'Python.bp': bp,
}

PRODUCTIONS = [
    {
        "dc.Python.Production": {
            "@Name": "dc.Python.Production",
            "@TestingEnabled": "true",
            "@LogGeneralTraceEvents": "false",
            "Description": "",
            "ActorPoolSize": "2"
        }
    }
]
