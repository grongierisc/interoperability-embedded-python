import bo, bp , bs, adapter

CLASSES = {
    "Python.FileOperation": bo.FileOperation,
    "Python.FileOperationWithIrisAdapter": bo.FileOperationWithIrisAdapter,
    "Python.EmailOperation": bo.EmailOperation,
    "Python.EmailOperationWithIrisAdapter": bo.EmailOperationWithIrisAdapter,
    "Python.RedditService": bs.RedditService,
    "Python.RedditServiceWithIrisAdapter": bs.RedditServiceWithIrisAdapter,
    "Python.RedditServiceWithPexAdapter": bs.RedditServiceWithPexAdapter,
    "Python.FilterPostRoutingRule": bp.FilterPostRoutingRule,
    "Python.TestHeartBeat": adapter.TestHeartBeat,
    "Python.HeartBeat": bo.HeartBeatOperation,
}

import os

PRODUCTIONS = [{
    "PEX.Production": {
        "@Name": "PEX.Production",
        "@TestingEnabled": "true",
        "@LogGeneralTraceEvents": "false",
        "Description": "",
        "ActorPoolSize": "2",
        "Item": [
            {
                "@Name": "Python.FileOperation",
                "@Category": "",
                "@ClassName": "Python.FileOperation",
                "@PoolSize": os.environ.get('POOL_SIZE', '1'),
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "true",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Adapter",
                        "@Name": "Charset",
                        "#text": "utf-8"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "FilePath",
                        "#text": "/irisdev/app/output/"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": "path=/tmp/"
                    }
                ]
            },
            {
                "@Name": "Python.FileOperationWithIrisAdapter",
                "@Category": "",
                "@ClassName": "Python.FileOperationWithIrisAdapter",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "true",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Adapter",
                        "@Name": "Charset",
                        "#text": "utf-8"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "FilePath",
                        "#text": "/irisdev/app/output/"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": "path=/irisdev/app/output/"
                    }
                ]
            },
            {
                "@Name": "Python.EmailOperation",
                "@Category": "",
                "@ClassName": "Python.EmailOperation",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "true",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Adapter",
                        "@Name": "SMTPPort"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "SMTPServer"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "SSLConfig"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "From"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "Credentials"
                    }
                ]
            },
            {
                "@Name": "Python.EmailOperationWithIrisAdapter",
                "@Category": "",
                "@ClassName": "Python.EmailOperationWithIrisAdapter",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "true",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Adapter",
                        "@Name": "SMTPPort"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "SMTPServer"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "SSLConfig"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "From"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "Credentials"
                    }
                ]
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
                "Setting": {
                    "@Target": "Host",
                    "@Name": "%settings",
                    "#text": "limit=10"
                }
            },
            {
                "@Name": "Python.RedditServiceWithIrisAdapter",
                "@Category": "",
                "@ClassName": "Python.RedditServiceWithIrisAdapter",
                "@PoolSize": "1",
                "@Enabled": "false",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Adapter",
                        "@Name": "Feed",
                        "#text": "/new/"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "Limit",
                        "#text": "4"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "SSLConfig",
                        "#text": "default"
                    }
                ]
            },
            {
                "@Name": "Python.RedditServiceWithPexAdapter",
                "@Category": "",
                "@ClassName": "Python.RedditServiceWithPexAdapter",
                "@PoolSize": "1",
                "@Enabled": "false",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": {
                    "@Target": "Adapter",
                    "@Name": "%settings",
                    "#text": "limit=3"
                }
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
}]