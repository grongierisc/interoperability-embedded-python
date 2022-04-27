# 1. interoperability-embedded-python

This proof of concept aims to show how the **iris interoperability framework** can be use with **embedded python**.

## 1.1. Table of Contents

- [1. interoperability-embedded-python](#1-interoperability-embedded-python)
  - [1.1. Table of Contents](#11-table-of-contents)
  - [1.2. Example](#12-example)
  - [1.3. Regsiter a component](#13-regsiter-a-component)
- [2. Demo](#2-demo)
- [3. Prerequisites](#3-prerequisites)
- [4. Installation](#4-installation)
  - [4.1. With Docker](#41-with-docker)
  - [4.2. Without Docker](#42-without-docker)
  - [4.3. With ZPM](#43-with-zpm)
- [5. How to Run the Sample](#5-how-to-run-the-sample)
- [6. What's inside the repository](#6-whats-inside-the-repository)
  - [6.1. Dockerfile](#61-dockerfile)
  - [6.2. .vscode/settings.json](#62-vscodesettingsjson)
  - [6.3. .vscode/launch.json](#63-vscodelaunchjson)
  - [6.4. .vscode/extensions.json](#64-vscodeextensionsjson)
  - [6.5. src folder](#65-src-folder)
- [7. How to add a new component](#7-how-to-add-a-new-component)
  - [7.1. InboundAdapter](#71-inboundadapter)
  - [7.2. OutboundAdapter](#72-outboundadapter)
  - [7.3. BusinessService](#73-businessservice)
  - [7.4. BusinessProcess](#74-businessprocess)
  - [7.5. BusinessOperation](#75-businessoperation)
  - [7.6. Regsiter a component](#76-regsiter-a-component)
  - [7.7. Direct use of Grongier.PEX](#77-direct-use-of-grongierpex)
- [8. Credits](#8-credits)

## 1.2. Example

```python
from grongier.pex import BusinessOperation,Message

class MyBusinessOperation(BusinessOperation):
    
    def on_init(self):
        #This method is called when the component is becoming active in the production
        print("[Python] ...MyBusinessOperation:on_init() is called")
        self.log_info("Operation on_init")
        return

    def OnTeardown(self):
        #This method is called when the component is becoming inactive in the production
        print("[Python] ...MyBusinessOperation:OnTeardown() is called")
        return

    def OnMessage(self,  message_input:MyRequest):
        # called from service/process/operation, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessOperation:OnMessage() is called with message:"+ message_input.requestString)
        self.log_info("Operation OnMessage")
        response = MyResponse("...MyBusinessOperation:OnMessage() echos")
        return response

@dataclass
class MyRequest(Message):

    requestString:str = None

@dataclass
class MyResponse(Message):

    myString:str = None

```

## 1.3. Regsiter a component 

Thanks to the method Grongier.PEX.Utils.RegisterComponent() : 

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.
```python
from grongier.pex import Utils

Utils.register_component(<ModuleName>,<ClassName>,<PathToPyFile>,<OverWrite>,<NameOfTheComponent>)
```

e.g :
```python
from grongier.pex import Utils

Utils.register_component("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
```

This is a hack, this not for production.
# 2. Demo

The production has four component in pure python :
 - Two Business Services :
   - Grongier.PEX.MyCombinedBusinessService, which sent continually sync messages to an business operation
     - Thoses messages are python objects cast JSON and stored in Grongier.PEX.Message.
     - Python code : src/python/demo/MyCombinedBusinessService.py
   - Grongier.PEX.MyBusinessService, who basically does nothing, it's a raw business service who writes message logs
     - Python code : src/python/demo/MyBusinessService.py
 - Two Business Operations :
   - Grongier.PEX.BusinessOperation, which receive message from Grongier.PEX.MyCombinedBusinessService
     - Python code : src/python/demo/MyBusinessOperation.py
   - Grongier.PEX.CombinedBusinessOperation, it can receive Ens.StringRequest message and response with Ens.StringResponse
     - Python code : src/python/demo/MyCombinedBusinessOperation.py

<img width="1177" alt="interop-screenshot" src="https://user-images.githubusercontent.com/47849411/131305197-d19511fd-6e05-4aec-a525-c88e6ebd0971.png">

New json trace for python native messages :

<img width="910" alt="json-message-trace" src="https://user-images.githubusercontent.com/47849411/131305211-b8beb2c0-438d-4afc-a6d2-f94d854373ae.png">

# 3. Prerequisites
Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Docker desktop](https://www.docker.com/products/docker-desktop) installed.

# 4. Installation 
## 4.1. With Docker

Clone/git pull the repo into any local directory

```sh
git clone https://github.com/grongierisc/interpeorability-embedded-python
```

Open the terminal in this directory and run:

```sh
docker-compose build
```

Run the IRIS container with your project:

```sh
docker-compose up -d
```

## 4.2. Without Docker

Install the *grongier_pex-1.2.4-py3-none-any.whl* on you local iris instance :

```sh
/usr/irissys/bin/irispython -m pip install grongier_pex-1.2.4-py3-none-any.whl
```

Then load the ObjectScript classes :

```ObjectScript
do $System.OBJ.LoadDir("/opt/irisapp/src","cubk","*.cls",1)
```
## 4.3. With ZPM 

```objectscript
zpm "install pex-embbeded-python" 
```

# 5. How to Run the Sample

Open the [production](http://localhost:52795/csp/irisapp/EnsPortal.ProductionConfig.zen?PRODUCTION=PEX.Production) and start it.
It will start running some code sample.

# 6. What's inside the repository

## 6.1. Dockerfile

A dockerfile which install some python dependancies (pip, venv) and sudo in the container for conviencies.
Then it create the dev directory and copy in it this git repository.

It starts IRIS and imports Titanics csv files, then it activates **%Service_CallIn** for **Python Shell**.
Use the related docker-compose.yml to easily setup additional parametes like port number and where you map keys and host folders.

This dockerfile ends with the installation of requirements for python modules.

The last part is about installing jupyter notebook and it's kernels.

Use .env/ file to adjust the dockerfile being used in docker-compose.

## 6.2. .vscode/settings.json

Settings file to let you immedietly code in VSCode with [VSCode ObjectScript plugin](https://marketplace.visualstudio.com/items?itemName=daimor.vscode-objectscript)

## 6.3. .vscode/launch.json
Config file if you want to debug with VSCode ObjectScript

[Read about all the files in this article](https://community.intersystems.com/post/dockerfile-and-friends-or-how-run-and-collaborate-objectscript-projects-intersystems-iris)

## 6.4. .vscode/extensions.json
Recommendation file to add extensions if you want to run with VSCode in the container.

[More information here](https://code.visualstudio.com/docs/remote/containers)

![Archiecture](https://code.visualstudio.com/assets/docs/remote/containers/architecture-containers.png)

This is very useful to work with embedded python.

## 6.5. src folder

```
src
├── Grongier
│   └── PEX // ObjectScript classes that wrap python code
│       ├── BusinessOperation.cls
│       ├── BusinessProcess.cls
│       ├── BusinessService.cls
│       ├── Common.cls
│       ├── Director.cls
│       ├── InboundAdapter.cls
│       ├── Message.cls
│       ├── OutboundAdapter.cls
│       ├── Python.cls
│       ├── Test.cls
│       └── Utils.cls
├── PEX // Some example of wrapped classes
│   └── Production.cls
└── python
    ├── demo // Actual python code to rnu this demo
    |   `-- reddit
    |       |-- adapter.py
    |       |-- bo.py
    |       |-- bp.py
    |       |-- bs.py
    |       |-- message.py
    |       `-- obj.py
    ├── dist // Wheel used to implement python interoperability components
    │   └── grongier_pex-1.2.4-py3-none-any.whl
    ├── grongier
    │   └── pex // Helper classes to implement interoperability components
    │       ├── _BusinessHost.py
    │       ├── _BusinessOperation.py
    │       ├── _BusinessProcess.py
    │       ├── _BusinessService.py
    │       ├── _Common.py
    │       ├── _Director.py
    │       ├── _InboundAdapter.py
    │       ├── _Message.py
    │       ├── _OutboundAdapter.py
    │       └── __init__.py
    └── setup.py // setup to build the wheel
```
# 7. How to add a new component

## 7.1. InboundAdapter

To implement InboundAdapter in Python, users do the following:

Subclass from grongier.pex.InboundAdapter in Python. Override method on_task().

## 7.2. OutboundAdapter

To implement OutboundAdapter in Python, users do the following:

Subclass from grongier.pex.OutboundAdapter in Python. Implement required action methods.

## 7.3. BusinessService

To implement BusinessService in Python, users do the following:

Subclass from grongier.pex.BusinessService in Python. Override method OnProcessInput().

## 7.4. BusinessProcess

To implement BusinessProcess in Python, users do the following:

Subclass from grongier.pex.BusinessProcess in Python. Override methods OnRequest(), OnResponse() and OnComplete().

## 7.5. BusinessOperation

To implement BusinessOperation in Python, users do the following:

Subclass from grongier.pex.BusinessOperation in Python. Override method OnMessage().

## 7.6. Regsiter a component 

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.
```python
from grongier.pex import Utils
Utils.register_component(<ModuleName>,<ClassName>,<PathToPyFile>,<OverWrite>,<NameOfTheComponent>)
```

e.g :
```python
from grongier.pex import Utils
Utils.register_component("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
```

## 7.7. Direct use of Grongier.PEX

If you don't want to use the RegisterComponent util. You can add an Grongier.PEX.Business* component and configure the properties :
- %module :
  - Module name of your python code
- %classname :
  - Classname of you component
- %classpaths
  - Path where you component is.
    - This can one or more Classpaths (separated by '|' character) needed in addition to PYTHON_PATH

e.g :

<img width="800" alt="component-config" src="https://user-images.githubusercontent.com/47849411/131316308-e1898b19-11df-433b-b1c6-7f69d5cc9974.png">

# 8. Credits

Most of the code came from PEX for Python by Mo Cheng and Summer Gerry.

The register part is from the not released feature form IRIS 2021.3.