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

## Business Service

Two kinds of business services can be created in Python:

- Business Service
- Pulling Business Service

### Business Service

To create a business service, use the following code:

```python
from iop import BusinessService

class MyBusinessService(BusinessService):
    
    def on_process_input(self, message_input: 'MyRequest'):
        # This method is called when the service is called
        self.log_info("[Python] MyBusinessService:on_process_input() is called with message: " + message_input.request_string)
        response = MyResponse("MyBusinessService:on_process_input() echos")
        return response
```

### Pulling Business Service

To create a business service that runs every 5 seconds, use the following code:

```python
from iop import BusinessService

class MyBusinessService(BusinessService):
    
    def get_adapter_type():
        # This is mandatory to schedule the service
        # By default, the service will be scheduled every 5 seconds
        return "Ens.InboundAdapter"

    def on_process_input(self):
        # This method is called every 5 seconds
        self.log_info("[Python] MyBusinessService:on_process_input() is called")
```

## Flask app sending a message to an Business Service

To send a message to a business service, use the following code:


```python
from flask import Flask, request
from iop import Director

app = Flask(__name__)

director = Director()

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.json
    bs = director.get_business_service("Python.MyBusinessService")
    resp = bs.on_process_input(message)
    return resp
```

## Business Process

To create a business process, use the following code:

```python
from iop import BusinessProcess

class MyBusinessProcess(BusinessProcess):
    
    def on_message(self, message_input: 'MyRequest'):
        # Called from service/process/operation, message is of type MyRequest with property request_string
        self.log_info("[Python] MyBusinessProcess:on_message() is called with message: " + message_input.request_string)
        response = MyResponse("MyBusinessProcess:on_message() echos")
        return response
```

### Async calls

There is three ways to make async calls in Python:

1. Using the `asyncio` library.
2. Using the native `send_request_async` method.
3. Using the `send_multi_request_sync` method.

#### Using the `asyncio` library

To make an async call with asyncio, use the following code:

```python
import asyncio
import random

from iop import BusinessProcess
from msg import MyMessage


class MyAsyncNGBP(BusinessProcess):

    def on_message(self, request):

        results = asyncio.run(self.await_response(request))

        for result in results:
            self.log_info(f"Received response: {result.message}")

    async def await_response(self, request):
        # create 1 to 10 messages
        tasks = []
        for i in range(random.randint(1, 10)):
            tasks.append(self.send_request_async_ng("Python.MyAsyncNGBO",
                                                    MyMessage(message=f"Message {i}")))

        return await asyncio.gather(*tasks)
```

#### Using the native `send_request_async` method

To make an async call with the native `send_request_async` method, use the following code:

```python
from grongier.pex import BusinessProcess
from msg import MyMessage


class MyBP(BusinessProcess):

    def on_message(self, request):
        msg_one = MyMessage(message="Message1")
        msg_two = MyMessage(message="Message2")

        self.send_request_async("Python.MyBO", msg_one,completion_key="1")
        self.send_request_async("Python.MyBO", msg_two,completion_key="2")

    def on_response(self, request, response, call_request, call_response, completion_key):
        if completion_key == "1":
            self.response_one = call_response
        elif completion_key == "2":
            self.response_two = call_response

    def on_complete(self, request, response):
        self.log_info(f"Received response one: {self.response_one.message}")
        self.log_info(f"Received response two: {self.response_two.message}")
```

#### Using the `send_multi_request_sync` method

To make an async call with the `send_multi_request_sync` method, use the following code:

```python
from iop import BusinessProcess
from msg import MyMessage


class MyMultiBP(BusinessProcess):

    def on_message(self, request):
        msg_one = MyMessage(message="Message1")
        msg_two = MyMessage(message="Message2")

        tuple_responses = self.send_multi_request_sync([("Python.MyMultiBO", msg_one),
                                                        ("Python.MyMultiBO", msg_two)])

        self.log_info("All requests have been processed")
        for target,request,response,status in tuple_responses:
            self.log_info(f"Received response: {response.message}")
```
