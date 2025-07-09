# IoP.Wrapper

IoP.Wrapper is a class designed to simplify the import of Python modules into InterSystems IRIS, providing remote debugging support and handling tracebacks effectively. It is particularly useful for developers who want to integrate Python code with IRIS while maintaining a smooth debugging experience.

## Features

- **Simplified Module Import**: Easily import Python modules into IRIS without complex configurations.
- **Remote Debugging Support**: Debug Python code running in IRIS from your local development environment.
- **Traceback Handling**: Automatically capture and format Python tracebacks for easier debugging.

## Usage

To use IoP.Wrapper, simply use the helper method `Import` to import your Python module. The method will handle the rest, including setting up the necessary environment for remote debugging and managing tracebacks.

```python
# my_script.py
import os

def main():
    # Get the value of the environment variable
    my_env_var = os.getenv('MY_ENV_VAR', 'default_value')
    
    # Print the value of the environment variable
    print(f'MY_ENV_VAR: {my_env_var}')

    return "Hello from my_script!"


if __name__ == "__main__":
    main()
```

The ObjectScript code to import the Python module would look like this:

```objectscript
Set pythonModule = "my_script"
Set pythonPath = "/path/to/your/python/scripts"
Set debugPort = 5678  ; Set the port for remote debugging
Set myModule = ##class(IoP.Wrapper).Import(pythonModule, pythonPath, debugPort)
// The process will automatically handle the import and setup for remote debugging and wait for the client debugger to attach.
// Once the client debugger is attached, you can run the main function of your Python module.
do myModule.main()
```

## Remarks

By the nature of python, to test it effectively, you must start a new job in IRIS each time you modify the Python code. This is because the Python interpreter does not automatically reload modules when they are changed, unlike some other languages (eg: objectscript).

For example, given the above code

```objectscript
Class Demo.PEX.NonProduction Extends %RegisteredObject
{

ClassMethod WrapperDemo() As %Status
{

    // Import the module
    set tModule = ##class(IOP.Wrapper).Import("my_script", "/path/to/your/python/scripts", 54132)
    
    // Call the function
    set result = tModule.main()

    // Print the result
    write result
}

}
```

You can run this objectscript code as :

```bash
iris session iris -U%IRISAPP '##class(Demo.PEX.NonProduction).WrapperDemo()'
```