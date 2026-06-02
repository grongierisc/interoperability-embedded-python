import os
from typing import Any


def get_iris(namespace: str | None = None) -> Any:
    if namespace:
        os.environ["IRISNAMESPACE"] = namespace
    import iris

    return iris
