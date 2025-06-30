# Registering Components

There are two main ways to register your Python components with IRIS Interoperability:

- With a settings file
    
- With a Python script:
    - Register a single component using `register_component`
    - Register all components in a file using `register_file` 
    - Register all components in a folder using `register_folder`

## With a Settings File

Create a `settings.py` file in the root of your project. This file will be used to register your classes and productions.

### Example of `settings.py`

```python
import bo

CLASSES = {
    "Python.MyBusinessOperation": bo.MyBusinessOperation
}
```

### Registering the Component

Use the `iop` command line to register your component:

```bash
iop --migrate /path/to/your/project/settings.py
```

## Using the Python Shell

### Registering a Single Component

Use the `register_component` method to add a new Python file to the component list for interoperability.

```python
from iop import Utils
Utils.register_component(<ModuleName>,<ClassName>,<PathToPyFile>,<OverWrite>,<NameOfTheComponent>)
```

Example:
```python
from iop import Utils
Utils.register_component("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
```

### Registering All Components in a File

Use the `register_file` method to add all components in a file to the component list for interoperability.

```python
from iop import Utils
Utils.register_file(<File>,<OverWrite>,<PackageName>)
```

Example:
```python
from iop import Utils
Utils.register_file("/irisdev/app/src/python/demo/bo.py",1,"PEX")
```

### Registering All Components in a Folder

Use the `register_folder` method to add all components in a folder to the component list for interoperability.

```python
from iop import Utils
Utils.register_folder(<Path>,<OverWrite>,<PackageName>)
```

Example:
```python
from iop import Utils
Utils.register_folder("/irisdev/app/src/python/demo/",1,"PEX")
```

### Migrating Settings

Use the `migrate` method to migrate the settings file to the IRIS framework.

```python
from iop import Utils
Utils.migrate()
```

## The `settings.py` File

This file is used to store the settings of the interoperability components. It has three sections:

- `CLASSES`: Stores the classes of the interoperability components.
- `PRODUCTIONS`: Stores the productions of the interoperability components.
- `SCHEMAS`: Stores the schemas of the interoperability components.

Example:
```python
import bp
from bo import *
from bs import *
from msg import RedditPost

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.FileOperation': FileOperation,
    'Python.FileOperationWithIrisAdapter': FileOperationWithIrisAdapter,
}

SCHEMAS = [RedditPost]

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
                "@PoolSize": "1",
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
```

### The `CLASSES` Section

This section stores the classes of the interoperability components. It helps to register the components.

The dictionary has the following structure:

- Key: The name of the component
- Value: 
  - The class of the component (you have to import it before)
  - The module of the component (you have to import it before)
  - Another dictionary with the following structure:
    - `module`: Name of the module of the component (optional)
    - `class`: Name of the class of the component (optional)
    - `path`: The path of the component (mandatory)

Example:

When Value is a class or a module:
```python
import bo
import bp
from bs import RedditService

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.FileOperation': bo,
}
```

When Value is a dictionary:
```python
CLASSES = {
    'Python.RedditService': {
        'module': 'bs',
        'class': 'RedditService',
        'path': '/irisdev/app/src/python/demo/'
    },
    'Python.Module': {
        'module': 'bp',
        'path': '/irisdev/app/src/python/demo/'
    },
    'Python.Package': {
        'path': '/irisdev/app/src/python/demo/'
    },
}
```

### The `PRODUCTIONS` Section

This section stores the productions of the interoperability components. It helps to register a production.

The list has the following structure:

- A list of dictionaries with the following structure:
  - `dc.Python.Production`: The name of the production
    - `@Name`: The name of the production
    - `@TestingEnabled`: The testing enabled of the production
    - `@LogGeneralTraceEvents`: The log general trace events of the production
    - `Description`: The description of the production
    - `ActorPoolSize`: The actor pool size of the production
    - `Item`: The list of the items of the production
      - `@Name`: The name of the item
      - `@Category`: The category of the item
      - `@ClassName`: The class name of the item
      - `@PoolSize`: The pool size of the item
      - `@Enabled`: The enabled of the item
      - `@Foreground`: The foreground of the item
      - `@Comment`: The comment of the item
      - `@LogTraceEvents`: The log trace events of the item
      - `@Schedule`: The schedule of the item
      - `Setting`: The list of the settings of the item
        - `@Target`: The target of the setting
        - `@Name`: The name of the setting
        - `#text`: The value of the setting

The minimum structure of a production is:
```python
PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Python.FileOperation",
                    },
                    {
                        "@Name": "Python.EmailOperation",
                        "@ClassName": "UnitTest.Package.EmailOperation"
                    }
                ]
            }
        } 
    ]
```

You can also set in `@ClassName` an item from the `CLASSES` section.

Example:
```python
from bo import FileOperation
PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": FileOperation,
                    }
                ]
            }
        } 
    ]
```

As the production is a dictionary, you can add in the value of the production dictionary an environment variable.

Example:
```python
import os

PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Python.FileOperation",
                        "Setting": {
                            "@Target": "Host",
                            "@Name": "%settings",
                            "#text": os.environ['SETTINGS']
                        }
                    }
                ]
            }
        } 
    ]
```

### The `SCHEMAS` Section

This section stores the schemas of the interoperability components. It helps to register the schemas for DTL transformations.

The list has the following structure:

- A list of classes

Example:
```python
from msg import RedditPost

SCHEMAS = [RedditPost]
```