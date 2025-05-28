import os
from typing import Optional

def get_iris(namespace: Optional[str]=None)->'iris': # type: ignore
    if namespace:
        os.environ['IRISNAMESPACE'] = namespace
    import iris
    return iris