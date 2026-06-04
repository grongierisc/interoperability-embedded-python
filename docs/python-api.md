# Python API Documentation

## Core Classes

### Message 📦
Base class for messages passed between components. This class provides the foundation for all message types in the interoperability framework.

**Usage:** Subclass `Message` and decorate with `@dataclass` to define message properties. This approach provides type hints and automatic initialization.

**Example:**
```python
from iop import Message
from dataclasses import dataclass

@dataclass
class MyRequest(Message):
    request_string: str = None
```

### PydanticMessage 📦

Base class for messages that use Pydantic models for validation and serialization. This class provides additional features for data validation and serialization.

**Usage:** Subclass `PydanticMessage` and define a Pydantic model as a class attribute. This approach provides automatic validation and serialization.

**Example:**
```python
from iop import PydanticMessage

class MyRequest(PydanticMessage):
    model : str = None
```

### PersistentMessage 📦

Base class for native IRIS message body classes backed by `iris-persistence`. Fields are declared directly on the Python class.

By default, a `PersistentMessage` generates an IRIS class that extends `Ens.MessageBody`, uses schema mode `extend`, and enables runtime auto-sync in extend mode.

**Example:**
```python
from iop import Field, Model, PersistentMessage

class Address(Model, serial=True):
    City: str

class OrderMessage(PersistentMessage):
    OrderId: str = Field(required=True, max_length=64)
    Amount: float = 0.0
    ShipTo: Address = None
```

You can give the IRIS class name explicitly with `Meta.classname`:
```python
class OrderMessage(PersistentMessage):
    OrderId: str = Field(required=True, max_length=64)

    class Meta:
        classname = "Demo.Msg.OrderMessage"
```

If no `Meta.classname` is declared, IOP derives a reversible IRIS-safe class name from the Python fully-qualified class name. Underscores are escaped as `zU`, literal `z` as `zz`, and unsupported characters as hexadecimal markers, then decoded again for incoming messages.

For migrations, you can also register the message with the IRIS classname as the `CLASSES` key:
```python
import msg

CLASSES = {
    "Demo.Msg.OrderMessage": msg.OrderMessage,
}
```

When `CLASSES` is used, migration writes message metadata parameters (`IOP_MESSAGE_KIND`, `IOP_PYTHON_CLASS`, and `IOP_PYTHON_CLASSPATH`) to the generated IRIS class. Incoming native IRIS message bodies use those parameters first, then fall back to the default naming convention when metadata is not present. If `Meta.classname` conflicts with the `CLASSES` key, migration fails.

### Message Dispatch

Business operations and business processes can route different message classes to different methods. Use `@handler(MessageType)` when you want the mapping to be explicit.

```python
from dataclasses import dataclass
from iop import BusinessOperation, Message, handler

@dataclass
class CreateOrder(Message):
    order_id: str = None

@dataclass
class CancelOrder(Message):
    order_id: str = None

class OrderOperation(BusinessOperation):
    @handler(CreateOrder)
    def create_order(self, request):
        return None

    @handler(CancelOrder)
    def cancel_order(self, request):
        return None
```

`MessageType` can be a Python message class or a fully-qualified class name string:

```python
class OrderOperation(BusinessOperation):
    @handler("orders.messages.CreateOrder")
    def create_order(self, request):
        return None
```

The decorated method should accept the incoming request as its only argument after `self`. A type annotation on the decorated method is optional because the decorator supplies the dispatch mapping.

If no `@handler` is declared for a message, IOP keeps the legacy behavior: public callable methods with one typed argument are added to the dispatch table automatically.

Dispatch priority is:

1. `@handler(MessageType)`
2. Explicit `DISPATCH` entries
3. Legacy typed-method discovery

When more than one mapping targets the same message type, IOP keeps the highest-priority mapping and logs a warning through the component warning logger, so the discarded handler appears in the IRIS logs. Duplicate mappings at the same priority keep the later entry for backward compatibility and log which earlier handler was discarded.

### BusinessService 🔄
Base class for business services that receive and process incoming data. Business services act as entry points for data into your interoperability solution.

**Key Methods:**

- `on_message(self, request: Message) -> Message | None`
    - Handles incoming service messages
    - Parameters:
        - `request`: The incoming message to process
    - Returns: Optional response message

- `on_process_input(self, message_input: Message | None = None) -> Message | None`
    - Low-level IRIS ProcessInput hook
    - By default, delegates to `on_message`

- `send_request_sync(self, target: str, request: Message, timeout: int = -1) -> Message`
    - Sends a synchronous request and waits for response
    - Parameters:
        - `target`: Name of the target component
        - `request`: Message to send
        - `timeout`: Maximum wait time in seconds (-1 for default)
    - Returns: Response message

- `send_request_async(self, target: str, request: Message) -> None`
    - Sends an asynchronous request without waiting
    - Parameters:
        - `target`: Name of the target component
        - `request`: Message to send
    - Returns: None

**Basic Example:**
```python
from iop import BusinessService

class MyService(BusinessService):
    def on_message(self, request):
        self.log_info(f"Received: {request}")
```

**Polling Example:**
```python
from iop import PollingBusinessService, Message
from dataclasses import dataclass

@dataclass
class MyRequest(Message):
    file_path: str = None
    data: str = None

class MyService(PollingBusinessService):
    InputFile = "/data/input.txt"

    def on_poll(self):
        with open(self.InputFile, 'r') as file:
            data = file.read()
        request = MyRequest(data=data)
        self.send_request_async("MyBusinessOperation", request)
```

`PollingBusinessService` uses the default IRIS inbound adapter. Override
`on_poll()` for scheduled polling, or override `on_process_input()` directly
when you need adapter-level access.

### Component Settings

Public class attributes on a component are exposed as IRIS production settings. By default they stay in the generated Python Attributes group. Use `setting(...)` when you want to control how a setting appears in the IRIS production UI.

```python
from iop import BusinessService, Category, controls, setting

class FileService(BusinessService):
    InputDirectory = setting(
        "/data/in",
        category=Category.CONNECTION,
        required=True,
        description="Directory to scan",
        control=controls.directory(),
    )

    Target = setting(
        "",
        category=Category.BASIC,
        required=True,
        control=controls.production_item(),
    )
```

You can also keep normal Python defaults and attach metadata with `typing.Annotated`:

```python
from typing import Annotated
from iop import BusinessService, Category, Setting, controls

class FramedService(BusinessService):
    Framing: Annotated[
        str,
        Setting(
            "None",
            category=Category.CONNECTION,
            control=controls.framing(),
        ),
    ]
```

#### Categories

Categories control where the setting appears in the IRIS production settings UI. They are written to the generated `SETTINGS` parameter as the setting section name. Categories do not change the Python attribute name, default value, IRIS data type, required flag, or editor control.

If `category` is omitted, the setting stays in the generated Python Attributes group. Use `Category` for common IRIS sections, or pass a string when a component needs its own section name.

```python
from iop import Category, setting

Timeout = setting(30, category=Category.BASIC)
ArchiveDirectory = setting("/archive", category="Archiving")
```

| Category | Generated section | Behavior |
| --- | --- | --- |
| `Category.INFO` | `Info` | Groups informational settings. Use for values that identify or describe the component rather than tune runtime behavior. |
| `Category.BASIC` | `Basic` | Groups the most common operational settings. Use for values a production operator is expected to review or change frequently. |
| `Category.CONNECTION` | `Connection` | Groups endpoint, path, credential, protocol, adapter, and network-related settings. |
| `Category.ADDITIONAL` | `Additional` | Groups optional or less frequently changed settings that should remain visible but not compete with the basic settings. |
| `Category.ALERTING` | `Alerting` | Groups alert, notification, and error-reporting settings. |
| `Category.DEV` | `Dev` | Groups development, debug, diagnostic, or troubleshooting settings. |
| `"Custom Name"` | `Custom Name` | Creates or uses a custom section with that exact name. Use sparingly so production settings stay predictable. |

#### Control Helpers

Control helpers return the IRIS production setting editor context string used in the generated `SETTINGS` parameter. They do not validate the selected value in Python; they tell the IRIS Management Portal which picker or selector to show for the setting.

| Helper | Returns | Behavior |
| --- | --- | --- |
| `controls.directory()` | `directorySelector` | Shows the IRIS directory picker. Use for settings that should contain a directory path. |
| `controls.file()` | `fileSelector` | Shows the IRIS file picker. Use for settings that should contain a file path. |
| `controls.production_item()` | `selector?context={Ens.ContextSearch/ProductionItems?targets=1&productionName=@productionId}` | Shows production items from the current production and stores the selected item name. Use for target component settings such as `TargetConfigName`. |
| `controls.credentials()` | `credentialsSelector` | Shows the credentials selector. Use for settings that reference an IRIS credentials entry. |
| `controls.rule()` | `ruleSelector` | Shows the rule selector. Use for settings that reference an IRIS rule definition. |
| `controls.dtl()` | `dtlSelector` | Shows the DTL selector. Use for settings that reference a data transformation. |
| `controls.schedule()` | `scheduleSelector` | Shows the schedule selector. Use for settings that reference an IRIS schedule. |
| `controls.ssl_config()` | `sslConfigSelector` | Shows the SSL/TLS configuration selector. Use for settings that reference an IRIS SSL configuration. |
| `controls.framing()` | `selector?context={Ens.ContextSearch/getDisplayList?host=@currHostId&prop=Framing}` | Shows the display list for the `Framing` property of the current host. Use for adapter framing settings. |
| `controls.character_set()` | `selector?context={Ens.ContextSearch/CharacterSets}` | Shows the IRIS character set selector. Use for charset or encoding settings. |
| `controls.local_interface()` | `selector?context={Ens.ContextSearch/TCPLocalInterfaces}` | Shows configured TCP local interfaces. Use for settings that bind to a local network interface. |
| `controls.schema_category(host)` | `selector?context={Ens.ContextSearch/SchemaCategories?host=<host>}` | Shows schema categories for the specified host. Pass a host expression such as `@currHostId` or a host setting value. |
| `controls.search_table(host)` | `selector?context={Ens.ContextSearch/SearchTableClasses?host=<host>}` | Shows search table classes for the specified host. Pass a host expression such as `@currHostId` or a host setting value. |

`controls.production_item()` accepts optional arguments:

```python
Target = setting(
    "",
    control=controls.production_item(
        targets=True,
        production_name="@productionId",
        multi_select=False,
    ),
)
```

- `targets`: passed to the IRIS `ProductionItems` context as `targets=1` or `targets=0`.
- `production_name`: passed to the IRIS `ProductionItems` context as `productionName=...`.
- `multi_select`: when `True`, adds `multiSelect=1` to the selector.

`controls.framing()` accepts optional arguments:

```python
Framing = setting(
    "None",
    control=controls.framing(host="@currHostId", prop="Framing"),
)
```

- `host`: host expression passed to `Ens.ContextSearch/getDisplayList`.
- `prop`: property name whose display list should be used.

For advanced IRIS controls, pass the raw editor context string:

```python
from iop import controls, setting

Framing = setting(
    "None",
    control=controls.raw(
        "selector?context={Ens.ContextSearch/getDisplayList?host=@currHostId&prop=Framing}"
    ),
)
```

### BusinessOperation 🔧
Base class for business operations that process requests and perform specific business logic.

**Key Methods:**

- `on_message(self, request: Message) -> Message`
    - Process incoming request messages
    - Parameters:
        - `request`: The incoming message to process
    - Returns: Response message

- `send_request_sync(self, target: str, request: Message, timeout: int = -1) -> Message`
    - Send synchronous request and wait for response
    - Parameters and returns same as BusinessService

- `send_request_async(self, target: str, request: Message) -> None`
    - Send asynchronous request without waiting
    - Parameters and returns same as BusinessService

**Example:**
```python
from dataclasses import dataclass
from iop import BusinessOperation, Message, handler

@dataclass
class MyRequest(Message):
    request_string: str = None

@dataclass
class MyResponse(Message):
    my_string: str = None

class MyOperation(BusinessOperation):
    @handler(MyRequest)
    def handle_my_request(self, request):
        self.log_info(f"Received: {request}")
        return MyResponse(my_string="Hello World")
```

### BusinessProcess ‍💼
Base class for business processes that orchestrate message flow between components.

**Key Methods:**

- `on_request(self, request: Message) -> None`
    - Handle initial incoming requests
    - Parameters:
        - `request`: The incoming request to process
    - Returns: None

- `on_response(self, request: Message, response: Message, call_request: Message, call_response: Message, completion_key: str) -> None`
    - Handle asynchronous responses
    - Parameters:
        - `request`: Original request
        - `response`: Current response
        - `call_request`: Request that generated this response
        - `call_response`: The response being processed
        - `completion_key`: Unique identifier for the response chain
    - Returns: None

- `on_complete(self, request: Message, response: Message) -> None`
    - Called after all responses are received
    - Parameters:
        - `request`: Original request
        - `response`: Final response
    - Returns: None

- `reply(self, response: Message) -> None`
    - Send response back to the caller
    - Parameters:
        - `response`: Response message to send
    - Returns: None

**Example:**
```python
from iop import BusinessProcess, Message
from dataclasses import dataclass

@dataclass
class MyRequest(Message):
    request_string: str = None

@dataclass
class MyResponse(Message):
    my_string: str = None

class MyProcess(BusinessProcess):
    def on_request(self, request):
        self.log_info(f"Received: {request}")
        self.send_request_async("MyBusinessOperation", request)

    def on_response(self, request, response, call_request, call_response, completion_key):
        self.log_info(f"Received: {response}")
        self.reply(response)
```

### Adapter Classes 🔌

#### InboundAdapter
Base class for adapters that receive external data.

**Key Methods:**

- `on_task(self) -> None`
    - Called at configured intervals to check for new data
    - Override this method to implement custom data acquisition logic
    - Returns: None

#### OutboundAdapter
Base class for adapters that send data to external systems.

**Key Methods:**

- `on_keepalive(self) -> None`
    - Called periodically to maintain external connections
    - Implement connection maintenance logic here
    - Returns: None


### Common Methods 🛠️
Available in all component classes:

**Logging Methods:**

- `log_info(self, message: str) -> None`
    - Log informational message for general information

- `log_error(self, message: str) -> None`
    - Log error message for errors and exceptions

- `log_warning(self, message: str) -> None`
    - Log warning message for potential issues

- `log_alert(self, message: str) -> None`
    - Log alert message for critical situations

**Lifecycle Methods:**

> **Warning:** Component constructors are not lifecycle hooks. IoP/IRIS
> allocates component instances with `__new__()` and does not call custom
> `__init__()` methods. Put startup logic in `on_init()`, and use class
> attributes or `iop.Setting` for configurable defaults.

- `on_init(self) -> None`
    - Initialize component when it starts
    - Override to add custom initialization

- `on_tear_down(self) -> None`
    - Clean up resources when component stops
    - Override to add custom cleanup logic

- `on_connected(self) -> None`
    - Handle connection setup when connections are established
    - Override to add custom connection logic


### Production Class

`Production` is the Pythonic authoring DSL for production topology.

```python
from iop import BusinessOperation, PollingBusinessService, Production, target

class FileService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        pass

class OrderOperation(BusinessOperation):
    def on_message(self, request):
        return request

prod = Production("Demo.Production")
file = prod.service("FileInput", FileService)
orders = prod.operation(OrderOperation)
prod.connect(file.Output, orders)
```

The same topology can be declared as a production subclass. Instantiating the
class returns a normal `Production` object, so `to_dict()`, `diff()`, `sync()`,
`apply()`, lifecycle methods, and migration all work the same way.

```python
from iop import OperationItem, Production, Route, ServiceItem


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


prod = DemoProduction()
```

For built-in IRIS or ObjectScript classes, pass the IRIS class name string:

```python
from iop import OperationItem, Production, Route, ServiceItem


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
```

`target()` declares a configurable outbound target setting on `FileService`.
`Route(FileService.Output, ORDER_OPERATION)` wires that setting to a production
item. This separation mirrors the instance-style form:
`prod.connect(file.Output, orders)`.

For Python component classes, prefer passing the descriptor
(`FileService.Output`) to `Route`. For built-in IRIS or ObjectScript classes,
there is no Python descriptor, so pass the IRIS setting name string such as
`"TargetConfigNames"`.

`Route(port, targets)` writes the Host setting for the port and records graph
edges by calling the same connection API used by instance-style authoring.
`targets` can be an item declaration, a string item name, or a sequence for
fan-out:

```python
AUDIT = OperationItem("AuditOperation", "Demo.AuditOperation")
ORDERS = OperationItem("OrderOperation", "Demo.OrderOperation")
Route("TargetConfigNames", (AUDIT, ORDERS))
```

Use `settings` or `host_settings` for non-route Host settings. Route ports
belong in `Route`; declaring the same port in Host settings raises an error.
Only known route aliases such as `target_config_names` are normalized to IRIS
names such as `TargetConfigNames`. Other Host and Adapter setting keys are
emitted exactly as supplied.

Use tuples for class-level `services`, `processes`, `operations`, and route
lists. Lists still work, but tuples avoid accidental mutation of shared class
attributes.

The same production can be authored progressively. Fluent methods mutate and
return the same `Production` or `ComponentRef`; there is no separate builder
object.

```python
prod = (
    Production("Demo.Production")
    .testing()
    .tracing()
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
```

For ObjectScript or built-in IRIS components, use manual port names:

```python
out = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

inp = (
    prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
    .adapter_setting("FilePath", "/tmp/in")
    .connect("TargetConfigNames", out)
)
```

Progressive production methods include `testing()`, `tracing()`,
`actor_pool()`, `describe()`, `timeouts()`, `alerting()`, `in_namespace()`,
and `with_director()`.
Progressive component methods include `pool()`, `enable()`, `disable()`,
`run_foreground()`, `trace()`, `schedule_on()`, `comment_as()`,
`category_as()`, `host_setting()`, `host_settings_update()`, `setting()`,
`settings_update()`, `adapter_setting()`, `adapter_settings_update()`,
`other_setting()`, `connect()`, and `connect_add()`.

`host_settings`, `adapter_settings`, and `foreground` are public data
attributes on `ComponentRef`, so their fluent update methods use distinct names
instead of shadowing those attributes.

Python `Production` is the source of truth for Python-authored topology. IRIS
remains the runtime source of truth. Imported graphs are operational
reconstructions until metadata persistence makes round-trip fidelity possible.

An IRIS production topology is modeled as a directed multigraph of possible
communication routes. A graph edge is a possible route between production
items, not a DAG execution dependency.

Key methods:

- `service()`, `process()`, `operation()`: add components to the Python graph
- `connect(port, component)`: connect a source `Port` to a target component
- `item(name)`: return a component reference by production item name
- `component_ref(target)`, `get_component(target)`: return a `ComponentRef`
  from an item name, component reference, port, or `"Item.Port"` path
- `graph()`: return a printable `ProductionGraph`
- `inspect_component(item)`: return component settings, routes, queue, and
  current runtime production status
- `start_component(item)`, `stop_component(item)`, `restart_component(item)`:
  manage one component through IRIS `EnableConfigItem`
- `test_component(item, message)`: test one component through the production
  graph
- `diff(other=None)`: compare deployable settings, items, and routes against
  another production or the deployed IRIS reconstruction
- `graph_diff(other=None)`: compare graph topology including edge origin and
  route metadata
- `validate(strict=False)`: report unknown production fields and invalid
  locally discoverable host/adapter settings. By default it emits warnings;
  strict mode raises `ProductionValidationError`.
- `plan(other=None)`: build a conservative granular change plan against another
  production or the deployed IRIS reconstruction
- `apply(plan=None)`: apply supported safe plan operations with a backup and
  fingerprint check. Destructive operations require `allow_destructive=True`.
- `verify(plan)`: re-export IRIS and report whether applied safe operations
  converged
- `rollback_backup(path, allow_destructive=True)`: restore a production from an
  apply backup directory
- `sync()`: register the current Python graph with local IRIS through the
  existing full-registration migration path

Production-level `Ens.Production` settings can be declared directly:

```python
prod = (
    Production("Demo.Production")
    .timeouts(shutdown=120, update=10)
    .alerting(
        manager="Alerts.Manager",
        operation="Alerts.Operation",
        recipients="ops@example.com",
        action_window=60,
    )
)
```

These values are serialized as production-level settings:
`ShutdownTimeout`, `UpdateTimeout`, `AlertNotificationManager`,
`AlertNotificationOperation`, `AlertNotificationRecipients`, and
`AlertActionWindow`.

`str(port)` returns the stable authoring identity, for example
`FileInput.Output`. Use `port.resolve()` when you explicitly need the current
IRIS dispatch target string.

`diff()` is directional: it reports changes needed to make the current/imported
state match the Python `Production` object.

```python
print(prod.diff())

runtime_prod = Production.from_iris("Demo.Production")
delta = prod.diff(runtime_prod)
if delta.has_changes:
    print(delta.to_dict())
```

ObjectScript and built-in IRIS components can be represented with `class_name`
and manual ports:

```python
file = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
out = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")
prod.connect(file.port("TargetConfigNames"), out)
```

For existing IRIS productions, use the conservative plan workflow instead of
assuming the Python object is a complete source of truth:

```python
from iop import ProductionChangePlan


plan = prod.plan()
print(plan)
plan.save("plan.json")

reviewed = ProductionChangePlan.load("plan.json")
apply_result = prod.apply(reviewed, backup_dir=".iop/backups")
print(apply_result)

verify_result = prod.verify(reviewed)
print(verify_result)
```

`apply()` writes a backup before mutation and skips destructive operations by
default. Pass `allow_destructive=True` only after reviewing deletes, removals,
or class replacements:

```python
prod.apply(reviewed, allow_destructive=True, backup_dir=".iop/backups")
```

Rollback restores the full exported production saved in the backup directory:

```python
from iop import Production


Production.rollback_backup(
    ".iop/backups/20260604T120000Z-abc123def456",
    allow_destructive=True,
)
```

Remote REST apply and rollback are blocked in v1. See
[Production Change Workflow](production-change-workflow.md) for the full
policy, CLI workflow, and backup file layout.

`ComponentRef.component_class` is the Python business host implementation class.
It is not the adapter. Adapter metadata is exposed separately:

```python
file.adapter_class_name
prod.inspect_component(file)["adapter_class_name"]
```

For Python adapters that should be registered during migration, pass the adapter
class explicitly while the business host class still declares its adapter type
with `get_adapter_type()`:

```python
file = prod.service(
    "FileInput",
    FileService,
    adapter_class=FileInboundAdapter,
)
```

Runtime inspection is explicit:

```python
runtime_prod = Production.from_iris("Demo.Production")
print(runtime_prod.graph())
queues = runtime_prod.queue()
```

`from_iris()` reconstructs an operational view from IRIS export and runtime
connections. `queue()` returns point-in-time queue counters from IRIS; it is
runtime metadata and does not affect `to_dict()` or migration output.
`queue_info()` remains available as a compatibility alias.
Adapter metadata such as `adapter_class_name` is taken from runtime connection
metadata when IRIS can provide it, or inferred from loaded Python host classes.

Graph edges expose route metadata such as `origin` (`authored`, `runtime`, or
`inferred`) and `interaction`. `diff()` ignores that import metadata when the
deployable IRIS shape is equivalent; use `graph_diff()` when you need to compare
the reconstruction quality or route origin.

`prod.test_component("Item.Port", message)` resolves from the current
`Production` object graph only. For an already deployed production, first build
an operational reconstruction with `Production.from_iris(...)`, then call
`test_component()` on that object. `prod.test(...)` remains as a compatibility
alias.

Lifecycle helpers such as `prod.stop()`, `prod.restart()`, `prod.kill()`, and
`prod.update()` verify that IRIS currently points at the same production before
calling the underlying IRIS lifecycle method.

Component lifecycle helpers follow the same rule:

```python
orders = prod.component_ref("OrderOperation")
info = orders.inspect()
orders.stop()
orders.start()
orders.restart()
orders.test(OrderRequest(order_id="123"))

# equivalent production-level calls
prod.stop_component("OrderOperation")
prod.start_component("OrderOperation")
prod.restart_component(file.Output)
```

`inspect_component(...)` can take a component reference, item name, `Port`, or
`"Item.Port"` path. A port resolves to its configured target component.
`ComponentRef` is a Python handle to the production item, not the live IRIS host
instance.

### Migration Utilities

Use `register_component()` or `bind_component()` to create an IRIS proxy class
binding for a Python component:

```python
from iop import bind_component, register_component

register_component(
    "bo",
    "FileOperation",
    "/irisdev/app/src/python/demo",
    overwrite=1,
    iris_classname="Python.FileOperation",
)

# Alias with the same arguments.
bind_component(
    "bo",
    "FileOperation",
    "/irisdev/app/src/python/demo",
    overwrite=1,
    iris_classname="Python.FileOperation",
)
```

Use `unregister_component()` or `unbind_component()` to remove an IOP-generated
IRIS proxy class binding:

```python
from iop import unbind_component, unregister_component

unregister_component("Python.WrongOperation")
unbind_component("Python.WrongOperation")
```

This removes only the IRIS proxy class. It does not delete Python source files
or production items. If a production item still uses the proxy class, IRIS
refuses the operation and reports the references.

Use `list_bindings()` to inspect generated proxy classes:

```python
from iop import list_bindings

bindings = list_bindings()
unused = list_bindings(unused_only=True)
```

### Director Class 🎭
Manages InterSystems IRIS productions and business services, particularly for non-polling services.

**Key Methods:**

**Production Management:**

- `start_production(production_name: str = None) -> None`
    - Start a production
    - If no name provided, uses default production

- `stop_production() -> None`
    - Stop the currently running production

- `restart_production() -> None`
    - Restart the current production

- `shutdown_production() -> None`
    - Gracefully shutdown the production

- `status_production() -> dict`
    - Get current production status
    - Returns dictionary with production details

**Business Service Management:**

- `create_business_service(target: str) -> object`
    - Create an instance of a business service
    - Parameters:
        - `target`: Name of the business service in production
    - Returns: Business service instance

- `get_business_service(target: str) -> object`
    - Get an existing business service instance
    - Parameters:
        - `target`: Name of the business service in production
    - Returns: Business service instance

- `test_component(target: str, message=None, classname: str=None, body=None, restart: bool=False) -> object`
    - Test a production component
    - Parameters:
        - `target`: Component name
        - `message`: Optional message instance (local mode only)
        - `classname`: Optional message class name
        - `body`: Optional message body (JSON string or dict)
        - `restart`: If `True`, the target component is stopped and restarted before the test message is dispatched (remote mode only)
    - Returns: Component response

**Production Logging:**

- `log_production() -> None`
    - Start real-time production log monitoring
    - Press Ctrl+C to stop

- `log_production_top(top: int) -> None`
    - Display last N log entries
    - Parameters:
        - `top`: Number of entries to show

**Production Configuration:**

- `set_default_production(production_name: str) -> None`
    - Set the default production name

- `get_default_production() -> str`
    - Get the current default production name

**Example Usage:**

In a flask application :

```python
from iop import Director

from flask import Flask

app = Flask(__name__)

director = Director()

@app.route('/')
def hello_world():
    bs = director.get_business_service("MyBusinessService")
    return bs.on_process_input("Hello, World!")
```
