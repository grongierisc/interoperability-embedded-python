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

The migrate command migrate a production and classes with settings file.

Migrate command must take the absolute path of the settings file.

Settings file must be in the same folder as the python code.

```bash
iop -M /tmp/settings.py
```

More details about the settings file can be found [here](getting-started/register-component.md).

## init

The init command initializes the IoP module in IRIS.

```bash
iop -i
```

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