
import threading
import time
import contextlib
import socket
from contextlib import closing

from typing import Optional, Tuple, Union, Sequence, cast, Callable, TypeVar, Dict, Any

def find_free_port(start: Optional[int] = None, end: Optional[int] = None) -> int:
    port = start
    if port is None:
        port = 0
    if end is None:
        end = port

    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            with contextlib.suppress(Exception):
                s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

            s.bind(("0.0.0.0", port))

            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return cast(int, s.getsockname()[1])
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException:
        if port and end > port:
            return find_free_port(port + 1, end)
        if start and start > 0:
            return find_free_port(None)
        raise


def is_debugpy_installed() -> bool:
    try:
        __import__("debugpy")
    except ImportError:
        return False
    return True


def wait_for_debugpy_connected(timeout: float = 30,port=0) -> bool:
    import debugpy  # noqa: T100

    if not is_debugpy_installed():
        return False

    class T(threading.Thread):
        daemon = True
        def run(self):
            time.sleep(timeout)
            debugpy.wait_for_client.cancel()
    T().start()
    debugpy.wait_for_client()
    if debugpy.is_client_connected():
        return True

    return False

def enable_debugpy(port: int, address = None) -> bool:

    import debugpy  # noqa: T100

    if address is None:
        address = "0.0.0.0"

    debugpy.listen((address, port))
