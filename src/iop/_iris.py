import os

def get_iris(namespace:str=None)->'iris':
    if namespace:
        os.environ['IRISNAMESPACE'] = namespace
    import iris
    return iris