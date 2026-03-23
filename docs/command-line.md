# Command line

Since version 2.3.1, you can use the command line to register your components and productions.

To use it, you have to use the following command :
```bash
iop 
```

output :
```bash
usage: python3 -m iop [-h] [-d DEFAULT] [-l] [-s START] [-S] [-k] [-r] [-x] [-m MIGRATE]
                      [-e EXPORT] [-v] [-L] [-i INIT] [-t TEST] [-D] [-C CLASSNAME] [-B BODY]

optional arguments:
  -h, --help            display help and default production name
  -d DEFAULT, --default DEFAULT
                        set the default production
  -l, --list           list productions
  -s START, --start START
                        start a production
  -S, --stop           stop a production
  -k, --kill           kill a production
  -r, --restart        restart a production
  -x, --status         status a production
  -m MIGRATE, -M MIGRATE, --migrate MIGRATE
                        migrate production and classes with settings file
  -e EXPORT, --export EXPORT
                        export a production
  -v, --version        display version
  -L, --log           display log
  -i INIT, --init INIT
                        init the pex module in iris
  -t TEST, --test TEST
                        test the pex module in iris

start arguments:
  -D, --detach         start a production in detach mode

test arguments:
  -C CLASSNAME, --classname CLASSNAME
                        test classname
  -B BODY, --body BODY
                        test body

default production: IoP.Production
```

## help

The help command display the help and the default production name.

```bash
iop -h
```

output :
```bash
usage: python3 -m iop [-h] [-d DEFAULT] [-l] [-s START] [-S] [-k] [-r] [-x] [-m MIGRATE]
                      [-e EXPORT] [-v] [-L] [-i INIT] [-t TEST] [-D] [-C CLASSNAME] [-B BODY]
...
default production: IoP.Production
```

## default

The default command set the default production.

With no argument, it display the default production.

```bash
iop -d
```

output :
```bash
default production: IoP.Production
```

With an argument, it set the default production.

```bash
iop -d IoP.Production
```

## list

The list command lists productions.

```bash
iop -l
```

output :
```bash
{
    "IoP.Production": {
        "Status": "Stopped",
        "LastStartTime": "2023-05-31 11:13:51.000",
        "LastStopTime": "2023-05-31 11:13:54.153",
        "AutoStart": 0
    }
}
```

## start

The start command starts a production.

To exit the command, you have to press CTRL+C (unless using detach mode).

```bash
iop -s IoP.Production
```

You can start a production in detach mode using the -D flag:

```bash
iop -s IoP.Production -D
```

In detach mode, the production starts and the command returns immediately without showing logs.

## kill

The kill command kill a production (force stop).

Kill command is the same as stop command but with a force stop.

Kill command doesn't take an argument because only one production can be running.

```bash
iop -k 
```

## stop

The stop command stop a production.

Stop command doesn't take an argument because only one production can be running.

```bash
iop -S 
```

## restart

The restart command restart a production.

Restart command doesn't take an argument because only one production can be running.

```bash
iop -r 
```

## migrate

The migrate command migrates a production and its classes using a settings file.

The settings file path can be relative or absolute.

```bash
iop -M /tmp/settings.py
```

More details about the settings file can be found [here](getting-started/register-component.md).

### Remote migrate

If the settings file contains a `REMOTE_SETTINGS` dict, the migration is performed against the remote IRIS instance automatically — no environment variables needed:

```python
# settings.py
REMOTE_SETTINGS = {
    "url": "http://localhost:52773",
    "username": "admin",
    "password": "password",
    "namespace": "USER",
}

CLASSES = { ... }
PRODUCTIONS = [ ... ]
```

To disable remote mode and run the migration locally even when `REMOTE_SETTINGS` is present or `IOP_URL` is set, pass `--force-local`:

```bash
iop -M /tmp/settings.py --force-local
```

`--force-local` disables remote mode for **all** commands, not only migrate.

## init

The init command initializes the IoP module in IRIS by loading and compiling the bundled `.cls` files.

```bash
iop -i
```

In **local mode** this calls `%SYSTEM.OBJ.LoadDir` + `%SYSTEM.OBJ.Compile` directly via the embedded Python binding.

In **remote mode** the same `.cls` files are uploaded file-by-file via the [Atelier REST API](https://docs.intersystems.com/iris20253/csp/documatic/%25CSP.Documatic.cls?LIBRARY=%25SYS&CLASSNAME=%25Api.Atelier.v1) (`PUT /api/atelier/v1/{namespace}/doc/{name}`) and then compiled in a single batch request (`POST /api/atelier/v1/{namespace}/action/compile`).

You can also point to a custom directory of `.cls` files:

```bash
iop -i /path/to/my/cls
```

### Remote init: Python package prerequisite

`iop -i` only handles the **ObjectScript side** (`.cls` files). The `iop` Python package itself must also be installed in the **remote IRIS Python environment** — the CLI cannot do this automatically because there is no REST endpoint to run `pip install` on the IRIS server.

Install it once on the server using the IRIS-bundled Python interpreter:

```bash
# On the machine running IRIS (or via docker exec / SSH)
python3 -m pip install iris-pex-embedded-python
```

> **Recommended init sequence for a fresh remote IRIS instance:**
> ```bash
> # 1. Upload and compile the .cls files via Atelier API
> iop -i
> 
> # 2. Install the iop Python package on the IRIS server (server-side, once)
> #    python3 -m pip install iris-pex-embedded-python
> 
> # 3. Now migrate your project
> iop -M /path/to/settings.py
> ```

## test

The test command allows testing IoP components. You can optionally specify a test name, classname, and body.

Basic test:
```bash
iop -t
```

Test with specific classname:
```bash
iop -t MyTest -C MyClass
```

Test with body:
```bash
iop -t MyTest -C MyClass -B "test body"
```

## export

The export command export a production.

If no argument is given, the export command export the default production.

```bash
iop -e
```

If an argument is given, the export command export the production given in argument.

```bash
iop -e IoP.Production
```

output :
```bash
{
    "Production": {
        "@Name": "IoP.Production",
        "@TestingEnabled": "true",
        "@LogGeneralTraceEvents": "false",
        "Description": "",
        "ActorPoolSize": "2",
        "Item": [
            {
                "@Name": "Python.FileOperation",
                "@Category": "",
                "@ClassName": "Python.FileOperation",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "true",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Adapter",
                        "@Name": "Charset",
                        "#text": "utf-8"
                    },
                    {
                        "@Target": "Adapter",
                        "@Name": "FilePath",
                        "#text": "/irisdev/app/output/"
                    },
                    {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": "path=/irisdev/app/output/"
                    }
                ]
            }
        ]
    }
}
```

## status

The status command status a production.

Status command doesn't take an argument because only one production can be running.

```bash
iop -x 
```

output :
```bash
{
    "Production": "IoP.Production",
    "Status": "stopped"
}
```

Status can be :
- stopped
- running
- suspended
- troubled

## version

The version command display the version.

```bash
iop -v
```

output :
```bash
2.3.0
```

## log

The log command display the log.

To exit the command, you have to press CTRL+C.

```bash
iop -L
```

output :
```bash
2021-08-30 15:13:51.000 [IoP.Production] INFO: Starting production
2021-08-30 15:13:51.000 [IoP.Production] INFO: Starting item Python.FileOperation
2021-08-30 15:13:51.000 [IoP.Production] INFO: Starting item Python.EmailOperation
...
```

## Remote mode

Since version 3.6.0, the `iop` CLI can operate against a **remote IRIS instance** (e.g. a Docker container or a server) without requiring a local IRIS installation.  All commands work in both local and remote mode.

### Activation

Remote mode is activated automatically through any of these mechanisms (evaluated in priority order):

1. **`IOP_URL` environment variable** — highest priority.
2. **`-R` / `--remote-settings` CLI flag** — path to a settings.py with `REMOTE_SETTINGS`.
3. **`IOP_SETTINGS` environment variable** — path to a Python file containing a `REMOTE_SETTINGS` dict.
4. **`-m settings.py` file** — when the file passed to the migrate command contains a `REMOTE_SETTINGS` dict, remote mode is enabled automatically for the entire command.

| Variable / flag | Description | Default |
|---|---|---|
| `IOP_URL` | Base URL of the IRIS web server (e.g. `http://localhost:52773`) | — |
| `-R FILE` / `--remote-settings FILE` | Path to a settings.py containing `REMOTE_SETTINGS` | — |
| `IOP_USERNAME` | IRIS username | — |
| `IOP_PASSWORD` | IRIS password | — |
| `IOP_NAMESPACE` | IRIS namespace to operate in | `USER` |
| `IOP_VERIFY_SSL` | Set to `false` to disable TLS certificate verification | `true` |
| `IOP_SETTINGS` | Path to a Python settings file containing a `REMOTE_SETTINGS` dict | — |

When none of the above resolve, the CLI operates in local mode (requires an active IRIS session).

### Quick start with Docker

```bash
# Point the CLI at the IRIS container
export IOP_URL=http://localhost:52773
export IOP_USERNAME=admin
export IOP_PASSWORD=password
export IOP_NAMESPACE=USER

iop -x            # production status
iop -l            # list all productions
iop -s MyApp.Production   # start a production
iop -r            # restart
iop -S            # stop
iop -k            # kill
iop -u            # update (hot-reload changed items)
iop -L            # tail the production log
```

### Settings file

You can store remote connection details in a Python `REMOTE_SETTINGS` dict and reference the file via the `-R` flag or the `IOP_SETTINGS` environment variable.

**Using the `-R` flag (recommended — takes priority over `IOP_SETTINGS`):**

```bash
iop -x -R /path/to/settings.py
iop -l -R /path/to/settings.py
iop -M /path/to/settings.py -R /path/to/settings.py   # explicit > migrate fallback
```

**Using the `IOP_SETTINGS` environment variable:**

```bash
export IOP_SETTINGS=/path/to/settings.py
```

The settings file format is the same either way:

```python
# settings.py — used by both migration and remote CLI
REMOTE_SETTINGS = {
    "url":        "http://iris-server:52773",
    "username":   "admin",
    "password":   "password",
    "namespace":  "USER",
    "verify_ssl": True,
}

# Optionally also define CLASSES / PRODUCTIONS for migration
CLASSES = { ... }
PRODUCTIONS = [ ... ]
```

This is the same file format used by `iop -m` for migrations, so a single `settings.py` can serve both purposes — describe which classes to register **and** how to reach the remote IRIS instance.

### Namespace override

You can override the namespace for a single command with the `-n` / `--namespace` flag:

```bash
iop -x -n MYNS
```

### Improved test command

In remote mode (and local mode) the `-t` command accepts a message body either inline or from a file:

```bash
# Inline JSON body
iop -t Python.MyOperation -C Python.MyRequest -B '{"key": "value"}'

# Body from a JSON file
iop -t Python.MyOperation -C Python.MyRequest -B @path/to/body.json
```

The response is pretty-printed:

```
classname: Python.MyResponse
body:
{
    "answer": 42
}
```

### Disabling remote mode

Pass `--force-local` to any command to bypass remote mode entirely, even when `IOP_URL`, `-R`, `IOP_SETTINGS`, or `REMOTE_SETTINGS` in a settings file would otherwise activate it:

```bash
iop -x --force-local               # status using local IRIS session
iop -M settings.py --force-local   # local migration, ignore REMOTE_SETTINGS
iop -L --force-local               # tail local log
iop -x -R settings.py --force-local  # -R is ignored when --force-local is set
```

### Current mode indicator

Running `iop -h` shows whether the CLI is in local or remote mode:

```
Mode: REMOTE (http://localhost:52773)
```
