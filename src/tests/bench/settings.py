from bo import BenchIoPOperation
from bp import BenchIoPProcess

import os

# get current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# get working directory
working_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
# get the absolute path of 'src'
src_dir = os.path.abspath(os.path.join(working_dir, os.pardir))

# create a strings with current_dir and src_dir with a | separator
classpaths = f"{current_dir}|{src_dir}"

CLASSES = {
    "Python.BenchIoPOperation": BenchIoPOperation,
    "Python.BenchIoPProcess": BenchIoPProcess,
}

PRODUCTIONS = [{
    "Bench.Production": {
        "@Name": "Bench.Production",
        "@TestingEnabled": "true",
        "@LogGeneralTraceEvents": "false",
        "Description": "",
        "ActorPoolSize": "1",
        "Item": [
            {
                "@Name": "Python.BenchIoPOperation",
                "@Category": "",
                "@ClassName": "Python.BenchIoPOperation",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": {
                    "@Target": "Host",
                    "@Name": "%classpaths",
                    "#text": classpaths
                }
            },
            {
                "@Name": "Python.BenchIoPProcess",
                "@Category": "",
                "@ClassName": "Python.BenchIoPProcess",
                "@PoolSize": "0",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": {
                    "@Target": "Host",
                    "@Name": "%classpaths",
                    "#text": classpaths
                }
            }
        ]
    }
}
]