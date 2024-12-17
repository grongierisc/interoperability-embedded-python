# IoP (Interoperability On Python)

[![PyPI - Status](https://img.shields.io/pypi/status/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI](https://img.shields.io/pypi/v/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI - License](https://img.shields.io/pypi/l/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
![GitHub last commit](https://img.shields.io/github/last-commit/grongierisc/interoperability-embedded-python)

Welcome to the **Interoperability On Python (IoP)** proof of concept! This project demonstrates how the **IRIS Interoperability Framework** can be utilized with a **Python-first approach**.

Documentation can be found [here](https://grongierisc.github.io/interoperability-embedded-python/).

## Example

Here's a simple example of how a Business Operation can be implemented in Python:

```python
from iop import BusinessOperation

class MyBo(BusinessOperation):
    def on_message(self, request):
        self.log_info("Hello World")
```

## Installation

To start using this proof of concept, install it using pip:

```bash
pip install iris-pex-embedded-python
```

## Getting Started

If you're new to this project, begin by reading the [installation guide](https://grongierisc.github.io/interoperability-embedded-python/getting-started/installation). Then, follow the [first steps](https://grongierisc.github.io/interoperability-embedded-python/getting-started/first-steps) to create your first Business Operation.

Happy coding!