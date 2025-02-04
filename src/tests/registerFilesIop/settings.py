import bp
from bo import *
from bs import RedditService
from message import SimpleMessage, PostMessage

SCHEMAS = [SimpleMessage, PostMessage]

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.bp': bp,
    'Python.FileOperation': FileOperation,
    'UnitTest.MySettingOperation': MySettingOperation,
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
    },
    {
        "Python.TestSettingProduction": {
            "@Name": "Python.TestSettingProduction",
            "@TestingEnabled": "true",
            "@LogGeneralTraceEvents": "false",
            "Description": "",
            "ActorPoolSize": "2",
            "Item": [
                {
                    "@Name": "UnitTest.MySettingOperation",
                    "@Enabled": "true",
                    "@ClassName": "UnitTest.MySettingOperation",
                    "Setting": [
                    {
                        "@Target": "Host",
                        "@Name": "my_int_var",
                        "#text": "1"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "my_float_var",
                        "#text": "1.0"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "my_untyped_var",
                        "#text": "1"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "my_str_var",
                        "#text": "bar"
                    }
                    ]
                }
            ]
        }
    }
]