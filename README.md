# IoP (Interoperability On Python)

[![PyPI - Status](https://img.shields.io/pypi/status/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI](https://img.shields.io/pypi/v/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI - License](https://img.shields.io/pypi/l/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
![GitHub last commit](https://img.shields.io/github/last-commit/grongierisc/interoperability-embedded-python)

Welcome to the **Interoperability On Python (IoP)** proof of concept! This project demonstrates how the **IRIS Interoperability Framework** can be utilized with a **Python-first approach**.

Documentation can be found [here](https://grongierisc.github.io/interoperability-embedded-python/).
For prompt-driven workflows, see [AI-assisted coding with IoP](https://grongierisc.github.io/interoperability-embedded-python/ai-coding/).
For task-oriented examples, see the [IoP cookbooks](https://grongierisc.github.io/interoperability-embedded-python/cookbooks/).
For application repositories, start from the [reusable AGENTS.md template](https://grongierisc.github.io/interoperability-embedded-python/agents-template/).

## Example

Here's a tiny Python-authored production:

```python
from dataclasses import dataclass

from iop import BusinessOperation, Message, PollingBusinessService, Production, target


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


prod = Production("HelloWorld.Production", testing_enabled=True)
service = prod.service("HelloService", HelloService)
operation = prod.operation("HelloOperation", HelloOperation)
prod.connect(service.Output, operation)

PRODUCTIONS = [prod]
```

## Installation

To start using this proof of concept, install it using pip:

```bash
pip install iris-pex-embedded-python
```

## Getting Started

If you're new to this project, begin by reading the [installation guide](https://grongierisc.github.io/interoperability-embedded-python/getting-started/installation). Then, follow the [first steps](https://grongierisc.github.io/interoperability-embedded-python/getting-started/first-steps) to create your first Python-authored production.

If you are using an AI coding assistant, start with [AI-assisted coding with IoP](https://grongierisc.github.io/interoperability-embedded-python/ai-coding/).
For concrete workflows, use the [IoP cookbooks](https://grongierisc.github.io/interoperability-embedded-python/cookbooks/).
For healthcare productions, also see [Healthcare AI-assisted coding](https://grongierisc.github.io/interoperability-embedded-python/healthcare-ai-coding/).

Happy coding!
