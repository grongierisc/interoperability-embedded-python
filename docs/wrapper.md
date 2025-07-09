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

