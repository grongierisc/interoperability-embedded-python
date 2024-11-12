# Command line

Since version 2.3.1, you can use the command line to register your components and productions.

To use it, you have to use the following command :
```bash
iop 
```

output :
```bash
usage: python3 -m iop [-h] [-d DEFAULT] [-l] [-s START] [-k] [-S] [-r] [-M MIGRATE] [-e EXPORT] [-x] [-v] [-L]
optional arguments:
  -h, --help            display help and default production name
  -d DEFAULT, --default DEFAULT
                        set the default production
  -l, --lists           list productions
  -s START, --start START
                        start a production
  -k, --kill            kill a production (force stop)
  -S, --stop            stop a production
  -r, --restart         restart a production
  -M MIGRATE, --migrate MIGRATE
                        migrate production and classes with settings file
  -e EXPORT, --export EXPORT
                        export a production
  -x, --status          status a production
  -v, --version         display version
  -L, --log             display log

default production: PEX.Production
```

## help

The help command display the help and the default production name.

```bash
iop -h
```

output :
```bash
usage: python3 -m iop [-h] [-d DEFAULT] [-l] [-s START] [-k] [-S] [-r] [-M MIGRATE] [-e EXPORT] [-x] [-v] [-L]
...
default production: PEX.Production
```

## default

The default command set the default production.

With no argument, it display the default production.

```bash
iop -d
```

output :
```bash
default production: PEX.Production
```

With an argument, it set the default production.

```bash
iop -d PEX.Production
```

## lists

The lists command list productions.

```bash
iop -l
```

output :
```bash
{
    "PEX.Production": {
        "Status": "Stopped",
        "LastStartTime": "2023-05-31 11:13:51.000",
        "LastStopTime": "2023-05-31 11:13:54.153",
        "AutoStart": 0
    }
}
```

## start

The start command start a production.

To exit the command, you have to press CTRL+C.

```bash
iop -s PEX.Production
```

output :
```bash
2021-08-30 15:13:51.000 [PEX.Production] INFO: Starting production
2021-08-30 15:13:51.000 [PEX.Production] INFO: Starting item Python.FileOperation
2021-08-30 15:13:51.000 [PEX.Production] INFO: Starting item Python.EmailOperation
...
```

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

## export

The export command export a production.

If no argument is given, the export command export the default production.

```bash
iop -e
```

If an argument is given, the export command export the production given in argument.

```bash
iop -e PEX.Production
```

output :
```bash
{
    "Production": {
        "@Name": "PEX.Production",
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
    "Production": "PEX.Production",
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
2021-08-30 15:13:51.000 [PEX.Production] INFO: Starting production
2021-08-30 15:13:51.000 [PEX.Production] INFO: Starting item Python.FileOperation
2021-08-30 15:13:51.000 [PEX.Production] INFO: Starting item Python.EmailOperation
...
```