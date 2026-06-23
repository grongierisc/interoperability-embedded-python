# Registering Components

Registering a Python component creates an IRIS proxy class that points to the
Python implementation. The CLI calls this a binding. Removing that proxy class
is called unbinding or unregistering; it does not delete Python source files or
production items.

For new applications, author a Python `Production` graph and put it in
`PRODUCTIONS`. IoP registers the Python component classes used by that graph
during migration.

## Production Graph

Create a migration file, usually named `settings.py`, in your project root:

```python
from dataclasses import dataclass

from iop import BusinessOperation, Message, PollingBusinessService, Production, target


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        self.send_request_async(self.Output, OrderRequest(order_id="777"))


class OrderOperation(BusinessOperation):
    def on_message(self, request: OrderRequest):
        self.log_info(f"Received order {request.order_id}")
        return request


prod = Production("Demo.Production", testing_enabled=True)
file = prod.service("FileInput", FileService)
orders = prod.operation("OrderOperation", OrderOperation)
prod.connect(file.Output, orders)

PRODUCTIONS = [prod]
```

Migrate it:

```bash
iop --migrate /path/to/your/project/settings.py
```

Migration registers the generated IRIS proxy classes for `FileService` and
`OrderOperation`, then saves `Demo.Production`.

`target()` declares a configurable outbound target setting on the component
class. `prod.connect(file.Output, orders)` sets that setting to the destination
component and records the production graph edge.

When you need to test `FileService` at runtime, do not use `iop --test`.
Business Service tests should go through the runtime director or production
runtime API so the deployed production context, component settings, and
configured targets are used.

## Settings File Sections

A migration file can define these sections:

| Section | Purpose |
|---------|---------|
| `PRODUCTIONS` | Preferred way to register Python-authored production graphs |
| `CLASSES` | Standalone or legacy component bindings and native `PersistentMessage` registrations |
| `SCHEMAS` | JSON schemas for DTL support |
| `REMOTE_SETTINGS` | Remote IRIS connection settings |

Regular `Message` and `PydanticMessage` classes do not go in `CLASSES`.
Register them in `SCHEMAS` only when you need DTL schema support.

## Native Persistent Messages

For Python-authored productions, declare native persistent messages on the
`Production` object:

```python
from iop import Field, PersistentMessage, Production


class OrderMessage(PersistentMessage):
    OrderId: str = Field(required=True)


prod = Production("Demo.Production")
prod.message("Demo.Msg.OrderMessage", OrderMessage)

PRODUCTIONS = [prod]
```

You can also register a native `PersistentMessage` in `CLASSES`. In this legacy
form, the dictionary key is the generated IRIS message body class name:

```python
from msg import OrderMessage


CLASSES = {
    "Demo.Msg.OrderMessage": OrderMessage,
}
```

## Standalone Bindings

Use `CLASSES` when you need to create an IRIS proxy class without putting the
component in a Python `Production` graph, usually for standalone bindings or
legacy migration files:

```python
from bo import FileOperation
from bs import RedditService


CLASSES = {
    "Python.RedditService": RedditService,
    "Python.FileOperation": FileOperation,
}
```

`CLASSES` values can be Python classes, imported modules, or dictionaries that
point at source files:

```python
CLASSES = {
    "Python.RedditService": {
        "module": "bs",
        "class": "RedditService",
        "path": "/irisdev/app/src/python/demo/",
    },
    "Python.Package": {
        "path": "/irisdev/app/src/python/demo/",
    },
}
```

## Legacy Production Dictionaries

Raw production dictionaries are still accepted for compatibility and for JSON
export round trips. Prefer `Production` objects for new Python-authored
topology.

Minimal legacy form:

```python
PRODUCTIONS = [
    {
        "Demo.Production": {
            "Item": [
                {
                    "@Name": "FileOperation",
                    "@ClassName": "Python.FileOperation",
                }
            ]
        }
    }
]
```

Legacy production dictionaries use the same keys as exported IRIS production
XML, such as `@Name`, `@ClassName`, `@PoolSize`, `@Enabled`, and `Setting`.

## Schemas

Register JSON schemas for DTL transformations with `SCHEMAS`:

```python
from msg import RedditPost


SCHEMAS = [RedditPost]
```

## Remote Migration

Add `REMOTE_SETTINGS` when migration should run against a remote IRIS instance:

```python
REMOTE_SETTINGS = {
    "url": "http://localhost:8080",
    "username": "admin",
    "password": "password",
    "namespace": "IRISAPP",
}
```

If the remote instance uses HTTPS with a self-signed certificate, disable SSL
verification only in development or trusted environments:

```python
REMOTE_SETTINGS = {
    "url": "https://localhost:8443",
    "username": "admin",
    "password": "password",
    "namespace": "IRISAPP",
    "verify_ssl": False,
}
```

Force local migration even when `REMOTE_SETTINGS` is present:

```bash
iop --migrate /path/to/settings.py --force-local
```

## Unbinding

If the wrong IRIS class name was used, remove the generated proxy class:

```bash
iop --unbind Python.WrongOperation
```

If a production item still uses that class, unbind fails and reports the
production item references. Remove or change those items before unbinding.

List generated proxy class bindings:

```bash
iop --bindings
iop --bindings --unused
```

## Python Shell Utilities

The Python utility functions remain available for scripting standalone
bindings and legacy/manual registration. The migration-file workflow with a
`Production` object in `PRODUCTIONS` is preferred for normal projects, and it
registers graph component classes automatically.

```python
from iop import bind_component, register_component


register_component(
    "bo",
    "FileOperation",
    "/irisdev/app/src/python/demo/",
    1,
    "Python.FileOperation",
)

bind_component(
    "bo",
    "FileOperation",
    "/irisdev/app/src/python/demo/",
    1,
    "Python.FileOperation",
)
```

Remove a binding from Python:

```python
from iop import unbind_component, unregister_component


unregister_component("Python.FileOperation")
unbind_component("Python.FileOperation")
```

Scan a file or folder for component classes:

```python
from iop import Utils


Utils.register_file("/irisdev/app/src/python/demo/bo.py", 1, "Python")
Utils.register_folder("/irisdev/app/src/python/demo/", 1, "Python")
```
