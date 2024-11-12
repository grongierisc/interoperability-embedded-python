# Example

Add an example of a business operation and messages in Python.

## Business Operation

Here is an example of a business operation in Python:

```python
from iop import BusinessOperation, Message
from dataclasses import dataclass

class MyBusinessOperation(BusinessOperation):
    
    def on_init(self):
        # This method is called when the component is becoming active in the production
        self.log_info("[Python] ...MyBusinessOperation:on_init() is called")
        return

    def on_teardown(self):
        # This method is called when the component is becoming inactive in the production
        self.log_info("[Python] ...MyBusinessOperation:on_teardown() is called")
        return

    def on_message(self, message_input: 'MyRequest'):
        # Called from service/process/operation, message is of type MyRequest with property request_string
        self.log_info("[Python] ...MyBusinessOperation:on_message() is called with message:" + message_input.request_string)
        response = MyResponse("...MyBusinessOperation:on_message() echos")
        return response

@dataclass
class MyRequest(Message):
    request_string: str = None

@dataclass
class MyResponse(Message):
    my_string: str = None
```

## Register a Component

To register a component, you need to create a setting.py file in the root of your project.

This file will be used to register your classes and productions.

Example of setting.py:

```python
import bo

CLASSES = {
    "Python.MyBusinessOperation": bo.MyBusinessOperation
}
```

Then you can use the iop command line to register your component:

```bash
iop --migrate /path/to/your/project/setting.py
```