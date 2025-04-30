
import threading
import time
import contextlib
import socket
import os
import sys
from contextlib import closing
from typing import Optional, cast, Any, Dict

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
        return True
    except ImportError:
        return False

def _get_python_interpreter_path(install_dir: Optional[str]) -> Optional[str]:
    """Get the path to the Python interpreter."""
    if not install_dir:
        return None
        
    python_exe = 'irispython.exe' if sys.platform == 'win32' else 'irispython'
    python_path = os.path.join(install_dir, 'bin', python_exe)
    
    return python_path if os.path.exists(python_path) else None

def _get_debugpy_config(python_path: str) -> Dict[str, str]:
    """Get the debugpy configuration."""
    return {"python": python_path}

def configure_debugpy(self, python_path: Optional[str] = None) -> bool:
    """Configure debugpy with the appropriate Python interpreter."""
    import debugpy

    if not python_path:
        install_dir = os.environ.get('IRISINSTALLDIR') or os.environ.get('ISC_PACKAGE_INSTALLDIR')
        python_path = _get_python_interpreter_path(install_dir)
        
    if not python_path:
        self.log_alert("Could not determine Python interpreter path")
        return False

    try:
        debugpy.configure(_get_debugpy_config(python_path))
        self.log_info(f"Debugpy configured with Python interpreter: {python_path}")
        return True
    except Exception as e:
        self.log_alert(f"Failed to configure debugpy: {e}")
        return False

def wait_for_debugpy_connected(timeout: float = 30, port: int = 0) -> bool:
    """Wait for debugpy client to connect."""
    import debugpy

    if not is_debugpy_installed():
        return False

    def timeout_handler():
        time.sleep(timeout)
        debugpy.wait_for_client.cancel()

    threading.Thread(target=timeout_handler, daemon=True).start()
    
    try:
        debugpy.wait_for_client()
        return debugpy.is_client_connected()
    except Exception:
        import pydevd # type: ignore
        pydevd.stoptrace()
        return False

def enable_debugpy(port: int, address: str = "0.0.0.0") -> None:
    """Enable debugpy server on specified port and address."""
    import debugpy
    debugpy.listen((address, port))

def debugpython(self, host_object: Any) -> None:
    """Enable and configure debugpy for debugging purposes."""
    # hack to set __file__ for os module in debugpy
    # This is a workaround for the issue where debugpy cannot find the __file__ attribute of the os module.
    if not hasattr(os, '__file__'):
        setattr(os, '__file__', __file__)


    if host_object is None:
        self.log_alert("No host object found, cannot enable debugpy.")
        return

    if host_object.enable != 1:
        self.log_info("Debugpy is not enabled.")
        return

    if not is_debugpy_installed():
        self.log_alert("Debugpy is not installed.")
        return

    # Configure Python interpreter
    if host_object.PythonInterpreterPath != '':
        success = configure_debugpy(self, host_object.PythonInterpreterPath)
    else:
        success = configure_debugpy(self)

    if not success:
        return

    # Setup debugging server
    port = host_object.port if host_object.port and host_object.port > 0 else find_free_port()
    
    try:
        enable_debugpy(port=port)
        self.log_info(f"Debugpy enabled on port {port}")
        
        self.trace(f"Waiting {host_object.timeout} seconds for debugpy connection...")
        if wait_for_debugpy_connected(timeout=host_object.timeout, port=port):
            self.log_info("Debugpy connected successfully")
        else:
            self.log_alert(f"Debugpy connection timed out after {host_object.timeout} seconds")
    except Exception as e:
        self.log_alert(f"Error enabling debugpy: {e}")