# Example

This document provides an example of a business operation and messages in Python, along with instructions on how to register a component.

## Business Operation

Below is an example of a business operation in Python:

```python
from iop import BusinessOperation, Message
from dataclasses import dataclass

class MyBusinessOperation(BusinessOperation):
    
    def on_init(self):
        # This method is called when the component is becoming active in the production
        self.log_info("[Python] MyBusinessOperation:on_init() is called")
        return

    def on_teardown(self):
        # This method is called when the component is becoming inactive in the production
        self.log_info("[Python] MyBusinessOperation:on_teardown() is called")
        return

    def on_message(self, message_input: 'MyRequest'):
        # Called from service/process/operation, message is of type MyRequest with property request_string
        self.log_info("[Python] MyBusinessOperation:on_message() is called with message: " + message_input.request_string)
        response = MyResponse("MyBusinessOperation:on_message() echos")
        return response

@dataclass
class MyRequest(Message):
    request_string: str = None

@dataclass
class MyResponse(Message):
    my_string: str = None
```

### Explanation

- **on_init**: This method is called when the component becomes active in the production.
- **on_teardown**: This method is called when the component becomes inactive in the production.
- **on_message**: This method is called from service/process/operation, and it processes the incoming message of type `MyRequest`.

## Register a Component

To register a component, create a `setting.py` file in the root of your project. This file will be used to register your classes and productions.

### Example of `setting.py`

```python
import bo

CLASSES = {
    "Python.MyBusinessOperation": bo.MyBusinessOperation
}
```

### Registering the Component

Use the `iop` command line to register your component:

```bash
iop --migrate /path/to/your/project/setting.py
```
