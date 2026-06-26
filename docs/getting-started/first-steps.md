# Getting Started with Interoperability On Python

Welcome to the guide on getting started with Interoperability Embedded Python. This document will walk you through the initial steps to set up and begin using Python in your interoperability projects.

## Prerequisites

Before you begin, ensure you have the following:

- A working installation of InterSystems IRIS with Embedded Python configured
- Basic knowledge of Python programming

### Setting Up the Virtual Environment

To begin, you will need to set up a virtual environment for your Python project. A virtual environment is a self-contained directory that contains a Python installation for a particular version of Python, as well as any additional packages you may need for your project.

To create a virtual environment, run the following command in your terminal:

```bash
python -m venv .venv
```

This will create a new directory called `.venv` in your project directory, which will contain the Python interpreter and any packages you install.

Next, activate the virtual environment by running the following command:

For Unix or MacOS:

```bash
source .venv/bin/activate
```

For Windows:

```bash
.venv\Scripts\activate
```

You should now see the name of your virtual environment in your terminal prompt, indicating that the virtual environment is active.

### Installing Required Packages

With your virtual environment activated, you can now install any required packages for your project. To install a package, use the `pip` command followed by the package name. For example, to install the `iris-pex-embedded-python` package, run the following command:

```bash
pip install iris-pex-embedded-python
```

Init the application using the following command:

```bash
iop --init
```

This will install the package and any dependencies it requires.

## Hello World

Now that you have set up your virtual environment and installed the required packages, you are ready to create your first Interoperability production using Python.

### Create the Python Components

For this first production, we will create two Python components:

- a `PollingBusinessService` that sends a request
- a `BusinessOperation` that receives the request and writes "Hello World" to the logs

Create a project folder:

```bash
mkdir -p hello_world
touch hello_world/__init__.py
```

In this folder, create a new file named `components.py`.

This file contains the message, service, and operation classes.

```python
from dataclasses import dataclass

from iop import BusinessOperation, Message, PollingBusinessService, target


@dataclass
class HelloRequest(Message):
    text: str = "Hello World"


class HelloService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        self.send_request_async(self.Output, HelloRequest())


class HelloOperation(BusinessOperation):
    def on_message(self, request: HelloRequest):
        self.log_info(request.text)
        return request
```

Let's explain this code:

- `HelloRequest` is the message sent between components.
- `HelloService` inherits from `PollingBusinessService`, so IRIS calls `on_poll()` on its schedule.
- `Output = target()` declares an outbound target setting on the service.
- `HelloOperation` inherits from `BusinessOperation` and handles the incoming message in `on_message()`.

> **Warning:** Do not put component startup code in `__init__()`. IoP/IRIS
> allocates components with `__new__()` and calls `on_init()` as the startup
> lifecycle hook.

### Declare the Production

Now, create `settings.py` at the root of your project.

This file is the migration entrypoint. It creates a `Production` object, adds the Python components, connects the service target to the operation, and exports the production through `PRODUCTIONS`.

```python
from iop import Production

from hello_world.components import HelloOperation, HelloService


prod = Production("HelloWorld.Production", testing_enabled=True)

service = prod.service("HelloService", HelloService)
operation = prod.operation("HelloOperation", HelloOperation)
service.connect(HelloService.Output, operation)

PRODUCTIONS = [prod]
```

In this production:

- `Production("HelloWorld.Production")` declares the IRIS production class.
- `prod.service("HelloService", HelloService)` adds one service item.
- `prod.operation("HelloOperation", HelloOperation)` adds one operation item.
- `service.connect(HelloService.Output, operation)` sets the service `Output` target to `HelloOperation` and records the production graph edge.
- `PRODUCTIONS = [prod]` tells IoP what to migrate.

You do not need a separate `CLASSES` dictionary for these production components. IoP registers Python component classes from the `Production` graph during migration.

### Migrate the Production

Run the migration command from the project root:

```bash
iop --migrate settings.py
```

This command creates the IRIS proxy classes for the Python components and registers `HelloWorld.Production`.

When you need to test `HelloService` at runtime, do not use `iop --test`.
Business Service tests should go through the runtime director or production
runtime API so the deployed production context, component settings, and
configured targets are used.

More information about registering components can be found [here](register-component.md).
