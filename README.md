## interoperability-embedded-python
This proof of concept aims to show how the **iris interoperability framework** can be use with **embedded python**.
This is a hack, this not for production.
Most of the code came from PEX for Python by Mo Cheng and Summer Gerry.
The register part is from the not released feature form IRIS 2021.3.

## What The Project Does ?

The production has four component :
 - Two Business Services :
   - Grongier.PEX.MyCombinedBusinessService, which sent continually sync messages to an business operation
   - Grongier.PEX.MyBusinessService, who basically does nothing, it's a raw business service
 - Two Business Operations :
   - Grongier.PEX.BusinessOperation, which receive message from Grongier.PEX.MyCombinedBusinessService
   - Grongier.PEX.CombinedBusinessOperation, it can receive Ens.StringRequest message and response with Ens.StringResponse

<img width="864" alt="Screenshot" src="https://raw.githubusercontent.com/grongierisc/interpeorability-embedded-python/master/misc/interop-screenshot.png"> 

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

## How to Run the Sample

Open the [production](http://localhost:52795/csp/irisapp/EnsPortal.ProductionConfig.zen?PRODUCTION=PEX.Production) and start it.
It will start running some code sample.

## How to add a new component

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
