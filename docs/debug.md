# Debug

How to debug IoP code. 

Before anything, I will put some context about IoP and IRIS.

Next I will show how to debug the code.

Finally, we will give some tips about debugging.

## Context

IoP is a Python library that helps to build interoperability solutions with IRIS.

IoP is based on [Embedded Python in IRIS](https://docs.intersystems.com/iris20243/csp/docbook/DocBook.UI.Page.cls?KEY=AFL_epython).

Embedded Python is a feature of IRIS that allows you to run Python code inside IRIS.

That means the python code is not running by a python interpreter, but by the IRIS process.

That comes with some limitations, like the lack of a debugger. It's planned to have a debugger in the future. eg: IRIS 2025.2+.

Meanwhile, we **have** some ways to debug the code.

## Debugging

Today (2025.2-), the best way to debug the code is to use an native python interpreter and run the code outside IRIS. This way you can use the python debugger.

The main issue with this approach is that you must have a local instance of IRIS to be able to run the code.

When I mean a local instance, it can be a local installation of IRIS, or a docker container running IRIS.

I will explain first with a local installation of IRIS. Then I will show how to do the same with a docker container.

### Local Installation

To debug the code with a local installation of IRIS, you need to have the following:

- A local installation of IRIS
  - https://docs.intersystems.com/irislatest/csp/docbook/Doc.View.cls?KEY=PAGE_deployment_install
- A python interpreter compatible with the version of IRIS
  - https://docs.intersystems.com/iris20243/csp/docbook/Doc.View.cls?KEY=GEPYTHON_prereqs#GEPYTHON_prereqs_version
- Iris embedded python wrapper
  - https://github.com/grongierisc/iris-embedded-python-wrapper

After you have all the requirements, you can start the IRIS instance and run the python code.

#### Debugging

To debug the code, you can use the python debugger.

Example with VsCode:

1. Open the code in VsCode to an existing folder.

For example, you can use this git repository:

```bash
git clone https://github.com/grongierisc/iris-python-interoperability-template
```

Open the folder `iris-python-interoperability-template` in VsCode.

```bash
code iris-python-interoperability-template
```

![Open the folder in VsCode](./img/vscode_open.png)

2. Install the python extension.

Go to the extensions tab and search for `Python`.

![Install the python extension](./img/vscode_python_extension.png)

3. Create a virtual environment and select it.

```bash
python -m venv .venv
source .venv/bin/activate
```

And select the virtual environment in VsCode.

![Select the virtual environment](./img/vscode_select_venv.png)

4. Install the dependencies.

```bash
pip install -r requirements.txt
```

5. Run the code in debug mode.

Open the file `src/python/reddit/bo.py`, put a breakpoint in the line 26.

![Put a breakpoint](./img/vscode_breakpoint.png)

And run the code in debug mode.

![Run the code in debug mode](./img/vscode_debug.png)

And you can debug the code.

![Debug the code](./img/vscode_debugging.png)

### Docker Container

The general idea is the same as the local installation.

The main difference is that you need to have a attached VSCode to the docker container.

For that, you can use the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.

Then you can attach the VSCode to the docker container and follow the same steps as the local installation.

## Tips

### Use unit tests

The best way to debug the code is to use unit tests.

You can use the python unittest library to write unit tests or pytest.

You have examples in [iris-python-interoperability-template](https://github.com/grongierisc/iris-python-interoperability-template/tree/master/src/python/tests).

### Use if __name__ == '__main__'

You can use the `if __name__ == '__main__':` to run the code only when you run the python file.

Example:

```python
def my_function():
    print('Hello World')

if __name__ == '__main__':
    my_function()
```

You also have examples in [iris-python-interoperability-template](https://github.com/grongierisc/iris-python-interoperability-template/blob/master/src/python/reddit/bo.py#L86).





