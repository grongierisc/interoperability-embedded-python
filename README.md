## interoperability-embedded-python
This proof of concept aims to show how the **iris interoperability framework** can be use with **embedded python**.
This is a hack, this not for production.

## What The Project Does ?

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

## Prerequisites
Make sure you have [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [Docker desktop](https://www.docker.com/products/docker-desktop) installed.

## Installation: Docker
Clone/git pull the repo into any local directory

```sh
git clone https://github.com/grongierisc/interpeorability-embedded-python
```

Open the terminal in this directory and run:

```sh
docker-compose build
```

3. Run the IRIS container with your project:

```sh
docker-compose up -d
```

## Installation without Docker

Install the *grongier_pex-1.0.0-py3-none-any.whl* on you local iris instance :

```sh
/usr/irissys/bin/irispython -m pip install grongier_pex-1.0.0-py3-none-any.whl
```

Then load the ObjectScript classes :

```ObjectScript
do $System.OBJ.LoadDir("/opt/irisapp/src","cubk","*.cls",1)
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

### Regsiter a component 

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

### Direct use of Grongier.PEX

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

## Future work

- Only Service and Operation has been tested.
- Work in progress on adapter

## Credits

Most of the code came from PEX for Python by Mo Cheng and Summer Gerry.
The register part is from the not released feature form IRIS 2021.3.