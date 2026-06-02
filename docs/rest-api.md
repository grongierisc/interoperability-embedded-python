# REST API

Since version 3.5.x+, IoP exposes a REST API that lets you manage productions, inspect logs, and test components remotely.

The API is served by the `IOP.Service.Remote.Rest.v1` CSP class and is mounted at `/api/iop` by default.

All endpoints return `application/json`. Errors are returned as:

```json
{"error": "<description>"}
```

---

## Namespace resolution

Every endpoint accepts an optional `namespace` parameter that selects the IRIS namespace to operate in (defaults to `USER`).

It can be supplied in two ways, which work on **all** routes:

| Method | Where to pass it | Example |
|--------|------------------|---------|
| Query string | `?namespace=IRISAPP` | `GET /api/iop/status?namespace=IRISAPP` |
| JSON body | `{"namespace": "IRISAPP", ...}` | `POST /api/iop/start` with body |

When both are present (POST/PUT routes), the **JSON body value takes priority** over the query string.

---

## GET /api/iop/version

Returns the API version and description.

**Response**

```json
{
  "version": "1.0.0",
  "description": "Interoperability Embedded Python Service API"
}
```

---

## GET /api/iop/status

Returns the currently running production name and its state.

**Query parameters**

| Parameter   | Type   | Default | Description            |
|-------------|--------|---------|------------------------|
| `namespace` | string | `USER`  | Target IRIS namespace  |

**Response**

```json
{
  "production": "MyApp.Production",
  "status": "running"
}
```

Possible `status` values: `running`, `stopped`, `suspended`, `troubled`, `unknown`.

---

## POST /api/iop/start

Starts a production.

**Namespace** — query string (`?namespace=`) or JSON body field (body wins).

**Request body** *(all fields optional)*

```json
{
  "production": "MyApp.Production"
}
```

| Field        | Required | Description                                              |
|--------------|----------|----------------------------------------------------------|
| `production` | No       | Production class name. Defaults to the last-used production. |

**Response**

```json
{
  "status": "started",
  "production": "MyApp.Production"
}
```

---

## POST /api/iop/stop

Stops the currently running production.

**Namespace** — query string (`?namespace=`) or optional JSON body field (body wins).

The request body may be omitted entirely.

**Response**

```json
{"status": "stopped"}
```

---

## POST /api/iop/kill

Forcefully stops the production (equivalent to `iop --kill`).

**Namespace** — query string (`?namespace=`) or optional JSON body field (body wins).

The request body may be omitted entirely.

**Response**

```json
{"status": "killed"}
```

---

## POST /api/iop/restart

Restarts the currently running production.

**Namespace** — query string (`?namespace=`) or optional JSON body field (body wins).

The request body may be omitted entirely.

**Response**

```json
{"status": "restarted"}
```

---

## POST /api/iop/update

Updates (hot-reloads) the currently running production.

**Namespace** — query string (`?namespace=`) or optional JSON body field (body wins).

The request body may be omitted entirely.

**Response**

```json
{"status": "updated"}
```

---

## GET /api/iop/list

Lists all productions in the namespace with their status metadata.

**Query parameters**

| Parameter   | Type   | Default | Description           |
|-------------|--------|---------|-----------------------|
| `namespace` | string | `USER`  | Target IRIS namespace |

**Response**

```json
{
  "MyApp.Production": {
    "Status": "Running",
    "LastStartTime": "2024-01-15 10:30:00",
    "LastStopTime": "2024-01-14 18:00:00",
    "AutoStart": true
  }
}
```

---

## GET /api/iop/default

Returns the default (last-used) production for the namespace.

**Query parameters**

| Parameter   | Type   | Default | Description           |
|-------------|--------|---------|-----------------------|
| `namespace` | string | `USER`  | Target IRIS namespace |

**Response**

```json
{"production": "MyApp.Production"}
```

---

## PUT /api/iop/default

Sets the default production for the namespace.

**Namespace** — query string (`?namespace=`) or JSON body field (body wins).

**Request body**

```json
{
  "production": "MyApp.Production"
}
```

**Response**

```json
{"production": "MyApp.Production"}
```

---

## GET /api/iop/log

Returns production log entries from `Ens_Util.Log`.

**Query parameters**

| Parameter  | Type    | Default | Description                                                        |
|------------|---------|---------|--------------------------------------------------------------------|
| `namespace`| string  | `USER`  | Target IRIS namespace                                              |
| `top`      | integer | `10`    | Number of most-recent entries to return (ignored when `since_id` is set) |
| `since_id` | integer | —       | Return only entries with `ID > since_id`, ordered ascending (useful for polling) |

**Response**

```json
[
  {
    "id": 42,
    "config_name": "MyService",
    "job": "12345",
    "message_id": "1",
    "session_id": "7",
    "source_class": "MyApp.Service",
    "source_method": "OnProcessInput",
    "text": "Processing request",
    "time_logged": "2024-01-15 10:30:01",
    "type": "Info"
  }
]
```

Possible `type` values: `Assert`, `Error`, `Warning`, `Info`, `Trace`, `Alert`, `Unknown`.

**Polling example**

```python
import requests

last_id = 0
while True:
    resp = requests.get(
        "http://localhost:52773/api/iop/log",
        params={"since_id": last_id, "namespace": "USER"},
        auth=("<USER>", "<PASSWORD>"),
    )
    entries = resp.json()
    for entry in entries:
        print(f"[{entry['type']}] {entry['config_name']}: {entry['text']}")
        last_id = entry["id"]
```

---

## GET /api/iop/export

Exports a production definition as JSON.

**Query parameters**

| Parameter    | Type   | Default              | Description                          |
|--------------|--------|----------------------|--------------------------------------|
| `namespace`  | string | `USER`               | Target IRIS namespace                |
| `production` | string | last-used production | Production class name to export      |

**Response**

```json
{
  "name": "MyApp.Production",
  "description": "",
  "test_enabled": true,
  "log_trace_events": false,
  "actor_pool_size": 2,
  "items": [
    {
      "name": "Python.MyOperation",
      "classname": "Python.MyOperation",
      "pool_size": 1,
      "enabled": true,
      "foreground": false,
      "comment": "",
      "log_trace_events": false,
      "schedule": "",
      "settings": [
        {"target": "Host", "name": "PythonClass", "value": "mymodule.MyOperation"}
      ]
    }
  ]
}
```

---

## GET /api/iop/connections

Exports runtime graph connections for a production. The endpoint calls
`OnGetConnections` for each production item, so it can report connections from
generated Python proxy classes, ObjectScript classes, and built-in `Ens.Host`
components.

**Query parameters**

| Parameter    | Type   | Default              | Description                          |
|--------------|--------|----------------------|--------------------------------------|
| `namespace`  | string | `USER`               | Target IRIS namespace                |
| `production` | string | last-used production | Production class name to inspect     |

**Response**

```json
{
  "production": "MyApp.Production",
  "items": [
    {
      "item": "FileInput",
      "class_name": "Python.demo.FileService",
      "adapter_class_name": "Ens.InboundAdapter",
      "connections": ["OrderOperation"],
      "warnings": []
    }
  ],
  "warnings": []
}
```

---

## GET /api/iop/queues

Exports runtime queue counters for production items. Queue data is runtime-only
metadata and is not written back to production XML.

**Query parameters**

| Parameter    | Type   | Default              | Description                          |
|--------------|--------|----------------------|--------------------------------------|
| `namespace`  | string | `USER`               | Target IRIS namespace                |
| `production` | string | last-used production | Production class name to inspect     |

**Response**

```json
{
  "production": "MyApp.Production",
  "items": [
    {
      "item": "FileInput",
      "queue_name": "FileInput",
      "class_name": "Python.demo.FileService",
      "exists": true,
      "count": 0
    }
  ],
  "warnings": []
}
```

---

## POST /api/iop/test

Sends a test message to a target component and returns the response synchronously.

**Namespace** — query string (`?namespace=`) or JSON body field (body wins).

**Request body**

```json
{
  "target":    "Python.MyOperation",
  "classname": "Python.MyMsg",
  "body":      {"key": "value"},
  "restart":   true
}
```

| Field       | Required | Description                                                                      |
|-------------|----------|----------------------------------------------------------------------------------|
| `target`    | Yes      | Config name of the component to invoke                                           |
| `classname` | No       | Python message class name. If omitted an empty `Ens.Request` is used.           |
| `body`      | No       | Message body — either a **JSON object** or a **JSON string**. Defaults to `{}`. |
| `restart`   | No       | If `true`, the target component is stopped and restarted before the message is dispatched. Useful to pick up code changes without restarting the whole production. |

**Response**

```json
{
  "classname": "Python.MyMsg",
  "body":      "{\"result\": \"ok\"}",
  "truncated": false
}
```

`truncated` is `true` when the response body was too large to return in full.

---

## POST /api/iop/component/start

Starts/enables one component in the current production runtime.

**Namespace** — query string (`?namespace=`) or JSON body field (body wins).

**Request body**

```json
{"component": "Python.MyOperation"}
```

`item` is accepted as an alias for `component`.

**Response**

```json
{"status": "started", "component": "Python.MyOperation"}
```

---

## POST /api/iop/component/stop

Stops/disables one component in the current production runtime.

**Request body**

```json
{"component": "Python.MyOperation"}
```

**Response**

```json
{"status": "stopped", "component": "Python.MyOperation"}
```

---

## POST /api/iop/component/restart

Restarts one component by disabling then enabling it.

**Request body**

```json
{"component": "Python.MyOperation"}
```

**Response**

```json
{"status": "restarted", "component": "Python.MyOperation"}
```

---

## DELETE /api/iop/binding

Removes one IOP-generated IRIS proxy class binding.

**Query parameters**

| Parameter   | Type   | Default | Description                     |
|-------------|--------|---------|---------------------------------|
| `namespace` | string | `USER`  | Target IRIS namespace           |
| `class`     | string | -       | IRIS proxy class name to remove |

`classname` is accepted as an alias for `class`.

**Response**

```json
{"status": "unbound", "class": "Python.WrongOperation"}
```

This endpoint only removes the generated IRIS proxy class. It does not delete
Python source files or production items. If any production item still uses the
proxy class, the endpoint fails and returns those production item references in
the error text.

---

## GET /api/iop/bindings

Lists IOP-generated IRIS proxy class bindings.

**Query parameters**

| Parameter   | Type    | Default | Description                                      |
|-------------|---------|---------|--------------------------------------------------|
| `namespace` | string  | `USER`  | Target IRIS namespace                            |
| `unused`    | boolean | `false` | Return only proxy classes unused by productions  |

**Response**

```json
[
  {
    "class": "Python.FileOperation",
    "super": "IOP.BusinessOperation",
    "module": "bo",
    "classname": "FileOperation",
    "classpaths": "/irisdev/app/src/python/demo",
    "used": true,
    "used_by": [
      {"production": "Demo.Production", "item": "FileOut"}
    ]
  }
]
```

---

## PUT /api/iop/migrate

Uploads a Python package to the server and runs its migration entrypoint. The
entrypoint defaults to `settings.py`, but clients can pass another Python file
name such as `demo.py`.

**Namespace** — query string (`?namespace=`) or JSON body field (body wins).

**Request body**

```json
{
  "namespace":     "USER",
  "remote_folder": "/opt/iris/packages",
  "package":       "my_package",
  "settings_file": "demo.py",
  "body": [
    {"name": "__init__.py",  "data": ""},
    {"name": "demo.py",  "data": "..."}
  ]
}
```

| Field           | Required | Description                                                                    |
|-----------------|----------|--------------------------------------------------------------------------------|
| `remote_folder` | No       | Absolute server path to place the package. Defaults to the namespace's routine DB directory. |
| `package`       | Yes      | Package directory name                                                         |
| `settings_file` | No       | Migration entrypoint file inside `body`. Defaults to `settings.py`.            |
| `body`          | Yes      | Array of `{name, data}` objects representing the files to write               |

**Response**

`200 OK` with an empty body on success.

---

## Authentication

The API uses standard IRIS CSP authentication. Pass credentials via HTTP Basic Auth:

```bash
curl -u <__USERNAME__>:<__PASSWORD__> http://localhost:52773/api/iop/status?namespace=USER
```

---

## Error responses

All endpoints return HTTP `500 Error` with a JSON body on failure:

```json
{"error": "<IRIS error string>"}
```
