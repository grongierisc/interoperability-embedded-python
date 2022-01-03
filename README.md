# interoperability-embedded-python
This proof of concept aims to show how the **iris interoperability framework** can be use with **embedded python**.

**No ObjectScript code is needed**.

Thanks to the method Grongier.PEX.Utils.RegisterComponent() : 
## Regsiter a component 

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.
```python
iris.cls("Grongier.PEX.Utils").RegisterComponent(<ModuleName>,<ClassName>,<PathToPyFile>,<OverWrite>,<NameOfTheComponent>)
```

e.g :
```python
iris.cls("Grongier.PEX.Utils").RegisterComponent("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
```

This is a hack, this not for production.

Example :

```python
import grongier.pex
import iris
import MyResponse

class MyBusinessOperation(grongier.pex.BusinessOperation):
    
    def OnInit(self):
        #OnInit method has it exists in objectscript
        #This method is called when the component is becoming active in the production
        print("[Python] ...MyBusinessOperation:OnInit() is called")
        self.LOGINFO("Operation OnInit")
        return

    def OnTeardown(self):
        #OnTeardown method has it exists in objectscript
        #This method is called when the component is becoming inactive in the production
        print("[Python] ...MyBusinessOperation:OnTeardown() is called")
        return

    def OnMessage(self, messageInput):
        # called from ticker service, message is of type MyRequest with property requestString
        print("[Python] ...MyBusinessOperation:OnMessage() is called with message:"+messageInput.requestString)
        self.LOGINFO("Operation OnMessage")
        response = MyResponse.MyResponse("...MyBusinessOperation:OnMessage() echos")
        return response
```
# Premade Demo

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

# Prerequisites
Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Docker desktop](https://www.docker.com/products/docker-desktop) installed.

# Installation with Docker
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

# Installation without Docker

Install the *grongier_pex-1.0.0-py3-none-any.whl* on you local iris instance :

```sh
/usr/irissys/bin/irispython -m pip install grongier_pex-1.0.0-py3-none-any.whl
```

Then load the ObjectScript classes :

```ObjectScript
do $System.OBJ.LoadDir("/opt/irisapp/src","cubk","*.cls",1)
```

# How to Run the Sample

Open the [production](http://localhost:52795/csp/irisapp/EnsPortal.ProductionConfig.zen?PRODUCTION=PEX.Production) and start it.
It will start running some code sample.

# What's inside the repository

## Dockerfile

A dockerfile which install some python dependancies (pip, venv) and sudo in the container for conviencies.
Then it create the dev directory and copy in it this git repository.

It starts IRIS and imports Titanics csv files, then it activates **%Service_CallIn** for **Python Shell**.
Use the related docker-compose.yml to easily setup additional parametes like port number and where you map keys and host folders.

This dockerfile ends with the installation of requirements for python modules.

The last part is about installing jupyter notebook and it's kernels.

Use .env/ file to adjust the dockerfile being used in docker-compose.

## .vscode/settings.json

Settings file to let you immedietly code in VSCode with [VSCode ObjectScript plugin](https://marketplace.visualstudio.com/items?itemName=daimor.vscode-objectscript)

## .vscode/launch.json
Config file if you want to debug with VSCode ObjectScript

[Read about all the files in this article](https://community.intersystems.com/post/dockerfile-and-friends-or-how-run-and-collaborate-objectscript-projects-intersystems-iris)

## .vscode/extensions.json
Recommendation file to add extensions if you want to run with VSCode in the container.

[More information here](https://code.visualstudio.com/docs/remote/containers)

![Archiecture](https://code.visualstudio.com/assets/docs/remote/containers/architecture-containers.png)

This is very useful to work with embedded python.

## src folder

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
│   ├── MyBusinessOperationWithAdapter.cls
│   ├── MyBusinessOperationWithIrisAdapter.cls
│   ├── MyBusinessOperationWithPythonAdapter.cls
│   ├── MyBusinessService.cls
│   ├── MyOutboundAdapter.cls
│   └── Production.cls
└── python
    ├── demo // Actual python code to rnu this demo
    │   ├── MyBusinessOperation.py
    │   ├── MyBusinessOperationWithAdapter.py
    │   ├── MyBusinessOperationWithIrisAdapter.py
    │   ├── MyBusinessProcess.py
    │   ├── MyBusinessService.py
    │   ├── MyCombinedBusinessOperation.py
    │   ├── MyCombinedBusinessProcess.py
    │   ├── MyCombinedBusinessService.py
    │   ├── MyInboundAdapter.py
    │   ├── MyLoggingOperation.py
    │   ├── MyNonPollingStarter.py
    │   ├── MyOutboundAdapter.py
    │   ├── MyRequest.py
    │   ├── MyResponse.py
    │   ├── MySyncBusinessProcess.py
    │   └── SimpleObject.py
    ├── dist // Wheel used to implement python interoperability components
    │   └── grongier_pex-1.0.0-py3-none-any.whl
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
# How to add a new component

## InboundAdapter

To implement InboundAdapter in Python, users do the following:

Subclass from grongier.pex.InboundAdapter in Python. Override method OnTask().

## OutboundAdapter

To implement OutboundAdapter in Python, users do the following:

Subclass from grongier.pex.OutboundAdapter in Python. Implement required action methods.

## BusinessService

To implement BusinessService in Python, users do the following:

Subclass from grongier.pex.BusinessService in Python. Override method OnProcessInput().

## BusinessProcess

To implement BusinessProcess in Python, users do the following:

Subclass from grongier.pex.BusinessProcess in Python. Override methods OnRequest(), OnResponse() and OnComplete().

## BusinessOperation

To implement BusinessOperation in Python, users do the following:

Subclass from grongier.pex.BusinessOperation in Python. Override method OnMessage().

## Regsiter a component 

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.
```python
iris.cls("Grongier.PEX.Utils").RegisterComponent(<ModuleName>,<ClassName>,<PathToPyFile>,<OverWrite>,<NameOfTheComponent>)
```

e.g :
```python
iris.cls("Grongier.PEX.Utils").RegisterComponent("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
```

## Direct use of Grongier.PEX

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

# Future work

- Only Service and Operation has been tested.
- Work in progress on adapter

# Credits

Most of the code came from PEX for Python by Mo Cheng and Summer Gerry.

The register part is from the not released feature form IRIS 2021.3.