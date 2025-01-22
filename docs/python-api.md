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

### BusinessService 🔄
Base class for business services that receive and process incoming data. Business services act as entry points for data into your interoperability solution.

**Key Methods:**

- `on_process_input(self, message_input: Message) -> None`
    - Handles incoming messages from adapter
    - Parameters:
        - `message_input`: The incoming message to process
    - Returns: None

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
    def on_process_input(self, message_input):
        self.log_info(f"Received: {message_input}")
```

**Advanced Example with Adapter:**
```python
from iop import BusinessService, Message
from dataclasses import dataclass

@dataclass
class MyRequest(Message):
    file_path: str = None
    data: str = None

class MyService(BusinessService):
    def get_adapter_type():
        """Enable pull mode for the BusinessService"""
        return "Ens.InboundAdapter"

    def on_process_input(self, message_input):
        self.log_info(f"Received: {message_input}")
        with open(message_input.file_path, 'r') as file:
            data = file.read()
        request = MyRequest(data=data)
        self.send_request_async("MyBusinessOperation", request)
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
from iop import BusinessOperation, Message
from dataclasses import dataclass

@dataclass
class MyRequest(Message):
    request_string: str = None

@dataclass
class MyResponse(Message):
    my_string: str = None

class MyOperation(BusinessOperation):
    def on_message(self, request):
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

- `on_init(self) -> None`
    - Initialize component when it starts
    - Override to add custom initialization

- `on_tear_down(self) -> None`
    - Clean up resources when component stops
    - Override to add custom cleanup logic

- `on_connected(self) -> None`
    - Handle connection setup when connections are established
    - Override to add custom connection logic


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

- `test_component(target: str, message=None, classname: str=None, body=None) -> object`
    - Test a production component
    - Parameters:
        - `target`: Component name
        - `message`: Optional message instance
        - `classname`: Optional message class name
        - `body`: Optional message body
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