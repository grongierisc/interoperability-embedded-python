import bp
from bo import *
from bs import RedditService

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.FileOperation': FileOperation,
    'Python.FileOperationWithIrisAdapter': {
        'file': 'FileOperationWithIrisAdapter.py',
        'class': 'FileOperationWithIrisAdapter',
        'module': 'bo',
        'path': 'src/tests/registerFiles'
    },
    'Python.bp': bp,
}

PRODUCTIONS = [
    {
        'dc.Python.Production': {
        "@Name": "dc.Demo.Production",
        "@TestingEnabled": "true",
        "@LogGeneralTraceEvents": "false",
        "Description": "",
        "ActorPoolSize": "2",
        "Item": [
            {
                "@Name": "Python.FileOperation",
                "@Category": "",
                "@ClassName": "Python.FileOperation",
                "@PoolSize": "",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "true",
                "@Schedule": "",
                "Setting": {
                    "@Target": "Host",
                    "@Name": "%settings",
                    "#text": "path=/tmp"
                }
            },
            {
                "@Name": "Python.RedditService",
                "@Category": "",
                "@ClassName": "Python.RedditService",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": "limit=10\nother<10"
                    }
                ]
            },
            {
                "@Name": "Python.FilterPostRoutingRule",
                "@Category": "",
                "@ClassName": "Python.FilterPostRoutingRule",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": ""
            }
        ]
    }
    }
]
