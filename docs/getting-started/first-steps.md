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

### Create a Business Operation

For this, we will create an `BusinessOperation` that will take a message as input and will return a message as output. In between, it will just print "Hello World" in the logs.

To do this, let's create a new folder named `hello_world`.

```bash
mkdir hello_world
```

In this folder, create a new file named `bo.py`.

This file will contain the code of our business operation.

```python
from iop import BusinessOperation

class MyBo(BusinessOperation):
    def on_message(self, request):
        self.log_info("Hello World")
```

Let's explain this code.

First, we import the `BusinessOperation` class from the `iop` module.

Then, we create a class named `MyBo` that inherits from `BusinessOperation`.

Finally, we override the `on_message` method. This method will be called when a message is received by the business operation.

### Import this Business Operation in the framework

Now, we need to add this business operation to what we call a production.

To do this, we will create a new file in the `hello_world` folder, named `settings.py`.

Every project starts at it's root folder by a file named `settings.py`. 

This file contains two main settings:

- `CLASSES` : it contains the classes that will be used in the project.
- `PRODUCTIONS` : it contains the name of the production that will be used in the project.

```python
from hello_world.bo import MyBo

CLASSES = {
    "MyIRIS.MyBo": MyBo
}

PRODUCTIONS = [
        {
            'MyIRIS.Production': {
                "@TestingEnabled": "true",
                "Item": [
                    {
                        "@Name": "Instance.Of.MyBo",
                        "@ClassName": "MyIRIS.MyBo",
                    }
                ]
            }
        } 
    ]
```

In this file, we import our `MyBo` class named in iris `MyIRIS.MyBo`, and we add it to the `CLASSES` dictionary.

Then, we add a new production to the `PRODUCTIONS` list. This production will contain our `MyBo` class instance named `Instance.Of.MyBo`.

With the `iop` command, we can now create the production in IRIS.

```bash
iop --migrate /path/to/hello_world/settings.py
```

This command will create the production in IRIS and add the `MyBo` class to it.

More information about registering components can be found [here](register-component.md).
