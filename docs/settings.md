# Settings Configuration

The migration file is the central configuration file for applying Python IOP
configuration to IRIS. It is commonly named `settings.py`, but it can be any
Python file, such as a single-file production named `demo.py`. It defines
classes, productions, schemas, and remote connection settings.

In this documentation, **migrate** means applying the file to IRIS. **Bind** or
**register** means creating an IRIS proxy class for a Python component.
**Unbind** or **unregister** means removing that generated proxy class. Unbind
does not delete Python source files or production items.

## Quick Start

Create a migration file in your project root:

```python
from iop import BusinessOperation, Production


class MyBusinessOperation(BusinessOperation):
    def on_message(self, request):
        self.log_info("Hello from IoP")
        return request


prod = Production("Demo.Production", testing_enabled=True)
prod.operation("MyBusinessOperation", MyBusinessOperation)

PRODUCTIONS = [prod]
```

Apply the migration file:
```bash
iop --migrate /path/to/your/project/settings.py
# or
iop --migrate /path/to/your/project/demo.py
```

If you bind a Python class to the wrong IRIS proxy class name, remove that
binding with:

```bash
iop --unbind Python.MyBusinessOperation
```

## Configuration Sections

The migration file supports four main sections:

| Section | Purpose |
|---------|---------|
| `PRODUCTIONS` | Define Python-authored production graphs with `Production` objects |
| `CLASSES` | Define standalone component bindings and native `PersistentMessage` classes |
| `SCHEMAS` | Register message schemas for DTL |
| `REMOTE_SETTINGS` | Configure remote IRIS connections |

## CLASSES Section

Use `CLASSES` for standalone component bindings that are not declared in a
Python `Production` graph. New Python-authored productions usually do not need
component entries in `CLASSES`; migration registers component classes from the
`Production` graph.

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

For Python-authored productions, you can declare native messages on the
`Production` object instead:

```python
from iop import Field, PersistentMessage, Production


class OrderMessage(PersistentMessage):
    OrderId: str = Field(required=True)


prod = Production("Demo.Production")
prod.message("Demo.Msg.OrderMessage", OrderMessage)

PRODUCTIONS = [prod]
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

The topology is modeled as a directed multigraph of possible communication
routes. A route edge is not a DAG execution dependency; it says that a component
may communicate with another component through a port or runtime route.

```python
from dataclasses import dataclass
from iop import BusinessOperation, Message, PollingBusinessService, Production, target


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        return self.send_request_sync(
            self.Output,
            OrderRequest(order_id="777"),
        )


class OrderOperation(BusinessOperation):
    def on_message(self, request):
        return request


prod = Production("Demo.Production", testing_enabled=True)
file = prod.service("FileInput", FileService)
orders = prod.operation(OrderOperation)
prod.connect(file.Output, orders)

PRODUCTIONS = [prod]
```

`target()` declares an outbound target setting on the component class.
`prod.connect()` sets that setting to the destination component and
records graph edges available to Python.

You can also write the same production as a class declaration. The class is a
template; put an instance in `PRODUCTIONS`.

```python
from dataclasses import dataclass
from iop import (
    BusinessOperation,
    Message,
    OperationItem,
    PollingBusinessService,
    Production,
    Route,
    ServiceItem,
    target,
)


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        return self.send_request_sync(
            self.Output,
            OrderRequest(order_id="777"),
        )


class OrderOperation(BusinessOperation):
    def on_message(self, request):
        return request


ORDER_OPERATION = OperationItem("OrderOperation", OrderOperation)


class DemoProduction(Production):
    name = "Demo.Production"
    testing_enabled = True

    services = (
        ServiceItem(
            "FileInput",
            FileService,
            routes=(Route(FileService.Output, ORDER_OPERATION),),
        ),
    )
    operations = (ORDER_OPERATION,)


PRODUCTIONS = [DemoProduction()]
```

For existing IRIS classes, use the IRIS class name string:

```python
FILE_OUT = OperationItem("FileOut", "EnsLib.File.PassthroughOperation")


class FileProduction(Production):
    name = "Demo.FileProduction"

    services = (
        ServiceItem(
            "FileIn",
            "EnsLib.File.PassthroughService",
            adapter_settings={"FilePath": "/tmp/in"},
            routes=(Route("TargetConfigNames", FILE_OUT),),
        ),
    )
    operations = (FILE_OUT,)


PRODUCTIONS = [FileProduction()]
```

`target()` declares the outbound target setting on the Python component class.
`Route(FileService.Output, ORDER_OPERATION)` wires that setting to a production
item. This is the class-style equivalent of `prod.connect(file.Output, orders)`.

For Python component classes, prefer the descriptor form
`Route(FileService.Output, ...)`. For existing IRIS classes, use the IRIS
setting name string, for example `Route("TargetConfigNames", "FileOut")`.

`Route(port, targets)` owns the route Host setting and records graph edges.
`targets` can be an item declaration, a string item name, or a sequence for
fan-out.
Use `settings` or `host_settings` only for non-route Host settings. If a route
port is also present in Host settings, migration raises an error so the route
stays explicit.

Use tuples for class-level `services`, `processes`, `operations`, and route
lists. Lists still work, but tuples avoid accidental mutation of shared class
attributes.

You can also author the same topology progressively:

```python
prod = (
    Production("Demo.Production")
    .testing()
    .actor_pool(2)
    .describe("Order ingestion")
)

orders = prod.operation(OrderOperation)

file = (
    prod.service("FileInput", FileService)
    .pool(2)
    .host_setting("Limit", 10)
    .adapter_setting("Charset", "utf-8")
    .connect("Output", orders)
)

PRODUCTIONS = [prod]
```

Progressive methods mutate the same `Production` and `ComponentRef` objects.
There is no separate public builder.

You can also reference existing ObjectScript or built-in IRIS components by
class name. These classes are not registered as Python components.

```python
prod = Production("Demo.Production")
file = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
out = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

prod.connect(file.port("TargetConfigNames"), out)
```

`ComponentRef.component_class` is the Python business host implementation class.
Adapter metadata is separate and exposed through `adapter_class_name`.
For Python adapter classes that should be registered automatically, pass
`adapter_class=...` when declaring the production item. The business host class
must still declare the adapter type with `get_adapter_type()` because IRIS stores
that adapter on the generated host class, not in production item XML.

Existing IRIS productions can be fetched back into the Python model:

```python
prod = Production.from_iris("Demo.Production")
print(prod.graph())
```

`from_iris()` reads the exported production definition and uses IRIS
`OnGetConnections` data when available. If runtime connection data cannot be
read, it falls back to Host settings whose value names another production item.
If runtime discovery returns no targets for an item, Host settings are still
used to draw inferred possible routes.
When available, runtime connection export also supplies adapter metadata such
as `adapter_class_name`; for loaded Python host classes this can also be
inferred from `get_adapter_type()`.
The fetched graph is an operational reconstruction, not a replacement for the
Python source. Python class objects are not recoverable from IRIS unless they
are also present in the Python source.

Runtime queue counters are separate from the authoring graph:

```python
prod = Production.from_iris("Demo.Production")
queues = prod.queue()
```

Queue data is point-in-time runtime information from IRIS. It is not serialized
by `prod.to_dict()` and does not change migration output. `prod.queue_info()`
remains available as a compatibility alias.

Diffing is explicit and directional:

```python
delta = prod.diff()
print(delta)
```

With no argument, `diff()` imports the deployed IRIS production and reports the
changes needed to make that runtime reconstruction match the Python
`Production` object. You can also pass another `Production` or an exported
production dictionary: `prod.diff(other_prod)`.

`diff()` compares the deployable production shape and ignores route import
metadata when the IRIS settings are equivalent. Use `prod.graph_diff(...)` to
compare graph metadata such as whether a route was authored in Python, imported
from runtime `OnGetConnections`, or inferred from Host settings.

`prod.test_component("Item.Port", message)` resolves from the current
`Production` object graph only. If you want to test a production that already
exists in IRIS, use `Production.from_iris(...)` first and call
`test_component()` on the imported operational reconstruction. `prod.test(...)`
remains available as a compatibility alias.

Lifecycle methods are scoped to the production object. `prod.stop()`,
`prod.restart()`, `prod.kill()`, and `prod.update()` verify that IRIS currently
points at the same production before invoking the underlying IRIS lifecycle
operation.

Component-level runtime management is also available:

```python
orders = prod.component_ref("OrderOperation")
info = orders.inspect()
orders.stop()
orders.start()
orders.restart()
orders.test(OrderRequest(order_id="123"))

# equivalent production-level calls
info = prod.inspect_component("OrderOperation")
prod.stop_component("OrderOperation")
prod.start_component("OrderOperation")
prod.restart_component(file.Output)
```

`inspect_component(...)` returns the component definition, incoming/outgoing
routes, queue counters when available, and the current runtime production
status. Component start/stop/restart is scoped to the same production object.
`ComponentRef` is a Python handle to a production item, not the live IRIS host
instance.

### Legacy Production Dictionaries

Raw production dictionaries are still accepted for compatibility and export
round trips. Prefer `Production` objects for new Python-authored topology.

#### Minimal Legacy Dictionary

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

#### Full Legacy Dictionary

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
- `@ClassName`: IRIS class name or class reference
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
from dataclasses import dataclass

from iop import BusinessOperation, Message, PollingBusinessService, Production, target


@dataclass
class RedditPost(Message):
    title: str = ""
    url: str = ""


class RedditService(PollingBusinessService):
    Output = target()
    Limit: int = 10

    def on_poll(self):
        self.send_request_async(
            self.Output,
            RedditPost(title="Latest post", url="https://example.invalid/post"),
        )


class FileOperation(BusinessOperation):
    def on_message(self, request: RedditPost):
        self.log_info(f"Exporting {request.title}")
        return request


# Remote connection settings
REMOTE_SETTINGS = {
    "url": "http://iris-server:8080",
    "username": "admin",
    "password": "password",
    "namespace": "IRISAPP"
}

# Optional DTL schema registration
SCHEMAS = [RedditPost]

# Production graph
prod = (
    Production("Reddit.Production", testing_enabled=True)
    .actor_pool(3)
    .describe("Reddit processing pipeline")
)

feed = (
    prod.service("RedditFeed", RedditService)
    .host_setting("Limit", int(os.environ.get("REDDIT_LIMIT", "10")))
)
exporter = prod.operation("FileExporter", FileOperation)
prod.connect(feed.Output, exporter)

PRODUCTIONS = [prod]
```

## Best Practices

1. **Use descriptive names** for components and productions
2. **Import modules at the top** of your settings file
3. **Use environment variables** for sensitive data and paths
4. **Group related components** in the same production
5. **Enable logging** during development and testing
6. **Document complex productions** with clear descriptions
