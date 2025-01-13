# Logging

InterSystems IRIS Interoperability framework implements its own logging system. The Python API provides a way to use Python's logging module integrated with IRIS logging.

## Basic Usage

The logging system is available through the component base class. You can access it via the `logger` property or use the convenience methods:

```python
def on_init(self):
    # Using convenience methods
    self.log_info("Component initialized")
    self.log_error("An error occurred")
    self.log_warning("Warning message")
    self.log_alert("Critical alert")
    self.trace("Debug trace message")

    # Using logger property
    self.logger.info("Info via logger")
    self.logger.error("Error via logger")
```

## Console Logging

You can direct logs to the console instead of IRIS in two ways:

1. Set the component-wide setting:
```python
def on_init(self):
    self.log_to_console = True
    self.log_info("This will go to console")
```

2. Per-message console logging:
```python
def on_message(self, request):
    # Log specific message to console
    self.log_info("Debug info", to_console=True)
    
    # Other logs still go to IRIS
    self.log_info("Production info")
```

## Log Levels

The following log levels are available:

- `trace()` - Debug level logging (maps to IRIS LogTrace)
- `log_info()` - Information messages (maps to IRIS LogInfo) 
- `log_warning()` - Warning messages (maps to IRIS LogWarning)
- `log_error()` - Error messages (maps to IRIS LogError)
- `log_alert()` - Critical/Alert messages (maps to IRIS LogAlert)
- `log_assert()` - Assert messages (maps to IRIS LogAssert)

## Integration with IRIS

The Python logging is automatically mapped to the appropriate IRIS logging methods:

- Python `DEBUG` → IRIS `LogTrace`
- Python `INFO` → IRIS `LogInfo`
- Python `WARNING` → IRIS `LogWarning` 
- Python `ERROR` → IRIS `LogError`
- Python `CRITICAL` → IRIS `LogAlert`

## Legacy Methods

The following methods are deprecated but maintained for backwards compatibility:

- `LOGINFO()` - Use `log_info()` instead
- `LOGALERT()` - Use `log_alert()` instead
- `LOGWARNING()` - Use `log_warning()` instead
- `LOGERROR()` - Use `log_error()` instead
- `LOGASSERT()` - Use `log_assert()` instead
