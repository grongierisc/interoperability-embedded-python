## interoperability-embedded-python
This proof of concept aims to show how the **iris interoperability framework** can be use with **embedded python**.
This is a hack, this not for production.
Most of the code came from PEX for Python by Mo Cheng and Summer Gerry.
The register part is from the not released feature form IRIS 2021.3.

## What The Project Does ?

The production has four component :
 - Two Business Services :
   - Grongier.PEX.MyCombinedBusinessService, which sent continually sync messages to an business operation
     - Thoses messages are python classes cast JSON and persoted in Grongier.PEX.Message.
   - Grongier.PEX.MyBusinessService, who basically does nothing, it's a raw business service
 - Two Business Operations :
   - Grongier.PEX.BusinessOperation, which receive message from Grongier.PEX.MyCombinedBusinessService
   - Grongier.PEX.CombinedBusinessOperation, it can receive Ens.StringRequest message and response with Ens.StringResponse

<img width="864" alt="Screenshot" src="https://raw.githubusercontent.com/grongierisc/interpeorability-embedded-python/master/misc/interop-screenshot.png"> 

New json trace for python native messages :

<img width="864" alt="Screenshot" src="https://raw.githubusercontent.com/grongierisc/interpeorability-embedded-python/master/misc/json-message-trace.png"> 

## Prerequisites
Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Docker desktop](https://www.docker.com/products/docker-desktop) installed.

## Installation: Docker
Clone/git pull the repo into any local directory

```
$ git clone https://github.com/grongierisc/interpeorability-embedded-python
```

Open the terminal in this directory and run:

```
$ docker-compose build
```

3. Run the IRIS container with your project:

```
$ docker-compose up -d
```

## Installation without Docker

Install the *grongier_pex-1.0.0-py3-none-any.whl* on you local iris instance :

```sh
/usr/irissys/bin/irispython -m pip install grongier_pex-1.0.0-py3-none-any.whl
```

Then load the ObjectScript classes :

```ObjectScript
do $System.OBJ.LoadDir("/opt/irisapp/src","ck",,1)
```

## How to Run the Sample

Open the [production](http://localhost:52795/csp/irisapp/EnsPortal.ProductionConfig.zen?PRODUCTION=PEX.Production) and start it.
It will start running some code sample.

## How to add a new component

### InboundAdapter

To implement InboundAdapter in Python, users do the following:

Subclass from grongier.pex.InboundAdapter in Python. Override method OnTask().

### OutboundAdapter

To implement OutboundAdapter in Python, users do the following:

Subclass from grongier.pex.OutboundAdapter in Python. Implement required action methods.

### BusinessService

To implement BusinessService in Python, users do the following:

Subclass from grongier.pex.BusinessService in Python. Override method OnProcessInput().

### BusinessProcess

To implement BusinessProcess in Python, users do the following:

Subclass from grongier.pex.BusinessProcess in Python. Override methods OnRequest(), OnResponse() and OnComplete().

### BusinessOperation

To implement BusinessOperation in Python, users do the following:

Subclass from grongier.pex.BusinessOperation in Python. Override method OnMessage().

### Regsiter an component 

Start a embedded python shell :

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

## Future work

- Only Service and Operation has been tested.
- Work in progress on adapter