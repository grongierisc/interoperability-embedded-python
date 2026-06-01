# Settings Configuration

The migration file is the central configuration file for registering your
interoperability components. It is commonly named `settings.py`, but it can be
any Python file, such as a single-file production named `demo.py`. It defines
classes, productions, schemas, and remote connection settings.

## Quick Start

Create a migration file in your project root:

```python
import bo

CLASSES = {
    "Python.MyBusinessOperation": bo.MyBusinessOperation
}
```

Register your components:
```bash
iop --migrate /path/to/your/project/settings.py
# or
iop --migrate /path/to/your/project/demo.py
```

## Configuration Sections

The migration file supports four main sections:

| Section | Purpose | Required |
|---------|---------|----------|
| `CLASSES` | Define interoperability components and native `PersistentMessage` classes | ✅ |
| `PRODUCTIONS` | Configure production workflows | ❌ |
| `SCHEMAS` | Register message schemas for DTL | ❌ |
| `REMOTE_SETTINGS` | Configure remote IRIS connections | ❌ |

## CLASSES Section

Register your interoperability components (BusinessOperations, BusinessProcesses, BusinessServices).

### Basic Usage

```python
import bo
from bs import RedditService

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FileOperation': bo.FileOperation,
}
```

`CLASSES` also registers native `PersistentMessage` schemas. In this case, the key is the generated IRIS message body classname:

```python
from msg import OrderMessage

CLASSES = {
    "Demo.Msg.OrderMessage": OrderMessage,
}
```

Regular `Message` and `PydanticMessage` classes do not go in `CLASSES` or
native message registration. Add them to `SCHEMAS` only when you need DTL schema
support.

## PRODUCTIONS Section

Define complete production configurations with multiple components.

### Pythonic Production

You can define productions with `Production` objects instead of raw dictionaries.
This is the authoring DSL for Python-defined topology: items, ports, settings,
and connections are declared in Python, then migration emits the same IRIS
production definition shape as the legacy dictionary format.

Python `Production` is the source of truth for Python-authored topology. IRIS
remains the runtime source of truth. Imported graphs are operational
reconstructions until metadata persistence makes round-trip fidelity possible.

```python
from dataclasses import dataclass
from iop import BusinessOperation, Message, PollingBusinessService, Production, target


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target("orders")

    def on_process_input(self, message_input):
        return self.send_request_sync(
            self.Output,
            OrderRequest(order_id="777"),
        )


class OrderOperation(BusinessOperation):
    pass


prod = Production("Demo.Production", testing_enabled=True)
file = prod.service("FileInput", FileService)
orders = prod.operation(OrderOperation)
prod.connect(file.Output, orders)

PRODUCTIONS = [prod]
```

`target()` declares an outbound port on the component class. `prod.connect()`
sets that port to the destination component for the generated production and
keeps graph metadata available to Python.

You can also reference existing ObjectScript or built-in IRIS components by
class name. These classes are not registered as Python components.

```python
prod = Production("Demo.Production")
file = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
out = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

prod.connect(file.port("TargetConfigNames"), out)
```

Existing IRIS productions can be fetched back into the Python model:

```python
prod = Production.from_iris("Demo.Production")
print(prod.graph())
```

`from_iris()` reads the exported production definition and uses IRIS
`OnGetConnections` data when available. If runtime connection data cannot be
read, it falls back to Host settings whose value names another production item.
The fetched graph is an operational reconstruction, not a replacement for the
Python source. Logical `target("orders")` names and Python class objects are not
recoverable from IRIS unless they are also present in the Python source.

Runtime queue counters are separate from the authoring graph:

```python
prod = Production.from_iris("Demo.Production")
queues = prod.queue()
```

Queue data is point-in-time runtime information from IRIS. It is not serialized
by `prod.to_dict()` and does not change migration output. `prod.queue_info()`
remains available as a compatibility alias.

### Minimal Production

```python
PRODUCTIONS = [
    {
        'MyApp.Production': {
            "@Name": "MyApp.Production",
            "Item": [
                {
                    "@Name": "FileProcessor",
                    "@ClassName": "Python.FileOperation",
                },
                {
                    "@Name": "EmailSender", 
                    "@ClassName": "Python.EmailOperation"
                }
            ]
        }
    }
]
```

### Full Production Configuration

```python
import os
from bo import FileOperation

PRODUCTIONS = [
    {
        'Demo.Production': {
            "@Name": "Demo.Production",
            "@TestingEnabled": "true",
            "@LogGeneralTraceEvents": "false",
            "Description": "Sample production for demonstration",
            "ActorPoolSize": "2",
            "Item": [
                {
                    "@Name": "FileProcessor",
                    "@ClassName": "Python.FileOperation",
                    "@PoolSize": "1",
                    "@Enabled": "true",
                    "@LogTraceEvents": "true",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": f"path={os.environ.get('DATA_PATH', '/tmp')}"
                    }
                }
            ]
        }
    }
]
```

**Production Attributes:**
- `@Name`: Production display name
- `@TestingEnabled`: Enable testing mode (`"true"`/`"false"`)
- `@LogGeneralTraceEvents`: Enable general logging
- `ActorPoolSize`: Number of concurrent actors

**Item Attributes:**
- `@Name`: Component instance name
- `@ClassName`: Class reference (from CLASSES or direct class)
- `@PoolSize`: Component pool size
- `@Enabled`: Enable/disable component
- `@LogTraceEvents`: Enable component-specific logging
- `Setting`: Component configuration settings

## SCHEMAS Section

Register message schemas for Data Transformation Language (DTL) operations.

```python
from msg import RedditPost, UserProfile

SCHEMAS = [RedditPost, UserProfile]
```

## REMOTE_SETTINGS Section

Configure connections to remote IRIS instances for component migration.

```python
REMOTE_SETTINGS = {
    "url": "http://localhost:8080",           # Required
    "username": "admin",                      # Optional
    "password": "password",                    # Optional  
    "namespace": "IRISAPP",                   # Optional (default: "USER")
    "remote_folder": "",                      # Optional (default: folder of the routine database)
    "package": "python",                      # Optional (default: "python")
    "verify_ssl": True                        # Optional (default: True)
}
```

**Configuration Options:**
- `url`: Remote IRIS instance URL (required)
- `username`: Authentication username
- `password`: Authentication password  
- `namespace`: Target namespace for components
- `remote_folder`: Remote storage folder
- `package`: Package name for components
- `verify_ssl`: Enable/disable SSL verification

## Complete Example

```python
import os
import bp
from bo import FileOperation, EmailOperation
from bs import RedditService
from msg import RedditPost

# Remote connection settings
REMOTE_SETTINGS = {
    "url": "http://iris-server:8080",
    "username": "admin",
    "password": "password",
    "namespace": "IRISAPP"
}

# Component registration
CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FileOperation': FileOperation,
    'Python.EmailOperation': EmailOperation,
    'Python.FilterRule': bp.FilterPostRoutingRule,
}

# Message schemas
SCHEMAS = [RedditPost]

# Production configuration
PRODUCTIONS = [
    {
        'Reddit.Production': {
            "@Name": "Reddit Processing Pipeline",
            "@TestingEnabled": "true",
            "ActorPoolSize": "3",
            "Item": [
                {
                    "@Name": "RedditFeed",
                    "@ClassName": "Python.RedditService",
                    "@Enabled": "true",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "%settings", 
                        "#text": f"limit={os.environ.get('REDDIT_LIMIT', '10')}"
                    }
                },
                {
                    "@Name": "PostFilter",
                    "@ClassName": "Python.FilterRule",
                    "@Enabled": "true"
                },
                {
                    "@Name": "FileExporter", 
                    "@ClassName": "Python.FileOperation",
                    "@Enabled": "true"
                }
            ]
        }
    }
]
```

## Best Practices

1. **Use descriptive names** for components and productions
2. **Import modules at the top** of your settings file
3. **Use environment variables** for sensitive data and paths
4. **Group related components** in the same production
5. **Enable logging** during development and testing
6. **Document complex productions** with clear descriptions
