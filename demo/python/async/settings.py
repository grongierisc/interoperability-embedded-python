from bo import MyBO
from bp import MyBP

CLASSES = {
    "Python.MyBO": MyBO,
    "Python.MyBP": MyBP,
}

PRODUCTIONS = [
    {
    "DemoAync.Production": {
        "@Name": "DemoAync.Production",
        "@TestingEnabled": "true",
        "@LogGeneralTraceEvents": "false",
        "Description": "",
        "ActorPoolSize": "2",
        "Item": [
            {
                "@Name": "UnitTest.MyOperation",
                "@Category": "",
                "@ClassName": "UnitTest.MyOperation",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": ""
            },
            {
                "@Name": "Python.Demo.MyBusinessOperation",
                "@Category": "",
                "@ClassName": "Python.Demo.MyBusinessOperation",
                "@PoolSize": "1",
                "@Enabled": "false",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": ""
            },
            {
                "@Name": "Python.MyBP",
                "@Category": "",
                "@ClassName": "Python.MyBP",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Host",
                        "@Name": "%enable",
                        "#text": "0"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "%port",
                        "#text": "54132"
                    }
                ]
            },
            {
                "@Name": "Python.MyBO",
                "@Category": "",
                "@ClassName": "Python.MyBO",
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