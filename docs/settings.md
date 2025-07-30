# Settings Configuration

The `settings.py` file is the central configuration file for registering your interoperability components. It defines classes, productions, schemas, and remote connection settings.

## Quick Start

Create a `settings.py` file in your project root:

```python
import bo

CLASSES = {
    "Python.MyBusinessOperation": bo.MyBusinessOperation
}
```

Register your components:
```bash
iop --migrate /path/to/your/project/settings.py
```

## Configuration Sections

The `settings.py` file supports four main sections:

| Section | Purpose | Required |
|---------|---------|----------|
| `CLASSES` | Define interoperability components | ✅ |
| `PRODUCTIONS` | Configure production workflows | ❌ |
| `SCHEMAS` | Register message schemas for DTL | ❌ |
| `REMOTE_SETTINGS` | Configure remote IRIS connections | ❌ |

## CLASSES Section

Register your interoperability components (BusinessOperations, BusinessProcesses, BusinessServices).

### Basic Usage

```python
import bo
from bs import RedditService

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FileOperation': bo.FileOperation,
}
```

## PRODUCTIONS Section

Define complete production configurations with multiple components.

### Minimal Production

```python
PRODUCTIONS = [
    {
        'MyApp.Production': {
            "@Name": "MyApp.Production",
            "Item": [
                {
                    "@Name": "FileProcessor",
                    "@ClassName": "Python.FileOperation",
                },
                {
                    "@Name": "EmailSender", 
                    "@ClassName": "Python.EmailOperation"
                }
            ]
        }
    }
]
```

### Full Production Configuration

```python
import os
from bo import FileOperation

PRODUCTIONS = [
    {
        'Demo.Production': {
            "@Name": "Demo.Production",
            "@TestingEnabled": "true",
            "@LogGeneralTraceEvents": "false",
            "Description": "Sample production for demonstration",
            "ActorPoolSize": "2",
            "Item": [
                {
                    "@Name": "FileProcessor",
                    "@ClassName": "Python.FileOperation",
                    "@PoolSize": "1",
                    "@Enabled": "true",
                    "@LogTraceEvents": "true",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": f"path={os.environ.get('DATA_PATH', '/tmp')}"
                    }
                }
            ]
        }
    }
]
```

**Production Attributes:**
- `@Name`: Production display name
- `@TestingEnabled`: Enable testing mode (`"true"`/`"false"`)
- `@LogGeneralTraceEvents`: Enable general logging
- `ActorPoolSize`: Number of concurrent actors

**Item Attributes:**
- `@Name`: Component instance name
- `@ClassName`: Class reference (from CLASSES or direct class)
- `@PoolSize`: Component pool size
- `@Enabled`: Enable/disable component
- `@LogTraceEvents`: Enable component-specific logging
- `Setting`: Component configuration settings

## SCHEMAS Section

Register message schemas for Data Transformation Language (DTL) operations.

```python
from msg import RedditPost, UserProfile

SCHEMAS = [RedditPost, UserProfile]
```

## REMOTE_SETTINGS Section

Configure connections to remote IRIS instances for component migration.

```python
REMOTE_SETTINGS = {
    "url": "http://localhost:8080",           # Required
    "username": "SuperUser",                  # Optional
    "password": "SYS",                        # Optional  
    "namespace": "IRISAPP",                   # Optional (default: "USER")
    "remote_folder": "",                      # Optional (default: folder of the routine database)
    "package": "python"                       # Optional (default: "python")
}
```

**Configuration Options:**
- `url`: Remote IRIS instance URL (required)
- `username`: Authentication username
- `password`: Authentication password  
- `namespace`: Target namespace for components
- `remote_folder`: Remote storage folder
- `package`: Package name for components

## Complete Example

```python
import os
import bp
from bo import FileOperation, EmailOperation
from bs import RedditService
from msg import RedditPost

# Remote connection settings
REMOTE_SETTINGS = {
    "url": "http://iris-server:8080",
    "username": "SuperUser", 
    "password": "SYS",
    "namespace": "IRISAPP"
}

# Component registration
CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FileOperation': FileOperation,
    'Python.EmailOperation': EmailOperation,
    'Python.FilterRule': bp.FilterPostRoutingRule,
}

# Message schemas
SCHEMAS = [RedditPost]

# Production configuration
PRODUCTIONS = [
    {
        'Reddit.Production': {
            "@Name": "Reddit Processing Pipeline",
            "@TestingEnabled": "true",
            "ActorPoolSize": "3",
            "Item": [
                {
                    "@Name": "RedditFeed",
                    "@ClassName": "Python.RedditService",
                    "@Enabled": "true",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "%settings", 
                        "#text": f"limit={os.environ.get('REDDIT_LIMIT', '10')}"
                    }
                },
                {
                    "@Name": "PostFilter",
                    "@ClassName": "Python.FilterRule",
                    "@Enabled": "true"
                },
                {
                    "@Name": "FileExporter", 
                    "@ClassName": "Python.FileOperation",
                    "@Enabled": "true"
                }
            ]
        }
    }
]
```

## Best Practices

1. **Use descriptive names** for components and productions
2. **Import modules at the top** of your settings file
3. **Use environment variables** for sensitive data and paths
4. **Group related components** in the same production
5. **Enable logging** during development and testing
6. **Document complex productions** with clear descriptions