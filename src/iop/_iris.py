import os
from typing import Any, Optional


def get_iris(namespace: Optional[str] = None) -> Any:
    if namespace:
        os.environ["IRISNAMESPACE"] = namespace
    import iris

    return iris
