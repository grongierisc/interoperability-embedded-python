# 1. interoperability-embedded-python

[![PyPI - Status](https://img.shields.io/pypi/status/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI](https://img.shields.io/pypi/v/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
[![PyPI - License](https://img.shields.io/pypi/l/iris-pex-embedded-python)](https://pypi.org/project/iris-pex-embedded-python/)
![GitHub last commit](https://img.shields.io/github/last-commit/grongierisc/interoperability-embedded-python)

This proof of concept aims to show how the **iris interoperability framework** can be use with **embedded python**.

## 1.1. Table of Contents

- [1. interoperability-embedded-python](#1-interoperability-embedded-python)
  - [1.1. Table of Contents](#11-table-of-contents)
  - [1.2. Example](#12-example)
  - [1.3. Register a component](#13-register-a-component)
- [2. Demo](#2-demo)
- [3. Installation](#3-installation)
  - [3.1. With ZPM](#31-with-zpm)
  - [3.2. With PyPI](#32-with-pypi)
    - [3.2.1. Known issues](#321-known-issues)
- [4. How to Run the Sample](#4-how-to-run-the-sample)
  - [4.1. Docker containers](#41-docker-containers)
  - [4.2. Management Portal and VSCode](#42-management-portal-and-vscode)
  - [4.3. Open the production](#43-open-the-production)
- [5. What's inside the repository](#5-whats-inside-the-repository)
  - [5.1. Dockerfile](#51-dockerfile)
  - [5.2. .vscode/settings.json](#52-vscodesettingsjson)
  - [5.3. .vscode/launch.json](#53-vscodelaunchjson)
  - [5.4. .vscode/extensions.json](#54-vscodeextensionsjson)
  - [5.5. src folder](#55-src-folder)
- [6. How it works](#6-how-it-works)
  - [6.1. The `__init__.py`file](#61-the-__init__pyfile)
  - [6.2. The `common` class](#62-the-common-class)
  - [6.3. The `business_host` class](#63-the-business_host-class)
  - [6.4. The `inbound_adapter` class](#64-the-inbound_adapter-class)
  - [6.5. The `outbound_adapter` class](#65-the-outbound_adapter-class)
  - [6.6. The `business_service` class](#66-the-business_service-class)
  - [6.7. The `business_process` class](#67-the-business_process-class)
  - [6.8. The `business_operation` class](#68-the-business_operation-class)
    - [6.8.1. The dispacth system](#681-the-dispacth-system)
    - [6.8.2. The methods](#682-the-methods)
  - [6.9. The `director` class](#69-the-director-class)
  - [6.10. The `objects`](#610-the-objects)
  - [6.11. The `messages`](#611-the-messages)
  - [6.12. How to regsiter a component](#612-how-to-regsiter-a-component)
    - [6.12.1. register\_component](#6121-register_component)
    - [6.12.2. register\_file](#6122-register_file)
    - [6.12.3. register\_folder](#6123-register_folder)
    - [6.12.4. migrate](#6124-migrate)
      - [6.12.4.1. setting.py file](#61241-settingpy-file)
        - [6.12.4.1.1. CLASSES section](#612411-classes-section)
        - [6.12.4.1.2. Productions section](#612412-productions-section)
  - [6.13. Direct use of IOP](#613-direct-use-of-iop)
- [7. Command line](#7-command-line)
  - [7.1. help](#71-help)
  - [7.2. default](#72-default)
  - [7.3. lists](#73-lists)
  - [7.4. start](#74-start)
  - [7.5. kill](#75-kill)
  - [7.6. stop](#76-stop)
  - [7.7. restart](#77-restart)
  - [7.8. migrate](#78-migrate)
  - [7.9. export](#79-export)
  - [7.10. status](#710-status)
  - [7.11. version](#711-version)
  - [7.12. log](#712-log)
- [8. Credits](#8-credits)

## 1.2. Example

bo.py
```python
from iop import BusinessOperation,Message

class MyBusinessOperation(BusinessOperation):
    
    def on_init(self):
        #This method is called when the component is becoming active in the production

        self.log_info("[Python] ...MyBusinessOperation:on_init() is called")

        return

    def on_teardown(self):
        #This method is called when the component is becoming inactive in the production

        self.log_info("[Python] ...MyBusinessOperation:on_teardown() is called")

        return

    def on_message(self, message_input:MyRequest):
        # called from service/process/operation, message is of type MyRequest with property request_string

        self.log_info("[Python] ...MyBusinessOperation:on_message() is called with message:"+message_input.request_string)

        response = MyResponse("...MyBusinessOperation:on_message() echos")

        return response

@dataclass
class MyRequest(Message):

    request_string:str = None

@dataclass
class MyResponse(Message):

    my_string:str = None

```

## 1.3. Register a component 

To register a component, you need to create a `setting.py` file in the root of your project.<br>

This file will be used to register your classes and productions.<br>

e.g.:
setting.py
```python
from iop import Utils

import bo

CLASSES = {
    "Python.MyBusinessOperation": bo.MyBusinessOperation
}
```

Then you can use the `iop` command line to register your component.

```sh
iop --migrate /path/to/your/project/setting.py
```

# 2. Demo

You can find a demo in the [src/python/demo](src/python/demo) folder.

Other demos are aviailable in those repositories:

  - [training](https://github.com/grongierisc/formation-template-python)
  - [template](https://github.com/grongierisc/iris-python-interoperability-template)
  - [falsk](https://github.com/grongierisc/iris-python-flask-api-template)
  - [rest-to-dicom](https://github.com/grongierisc/RestToDicom)

# 3. Installation

## 3.1. With ZPM 

```objectscript
zpm "install pex-embbeded-python" 
```

## 3.2. With PyPI

```sh
pip3 install iris-pex-embedded-python
```

Import the ObjectScript classes, open an embedded python shell and run :

```python
from iop import Utils
Utils.setup()
```

or use `iop` command line :

```sh
iop --init
```

### 3.2.1. Known issues

If the module is not updated, make sure to remove the old version :

```sh
pip3 uninstall iris-pex-embedded-python
```

or manually remove the `grongier` folder in `<iris_installation>/lib/python/`

or force the installation with pip :

```sh
pip3 install --upgrade iris-pex-embedded-python --target <iris_installation>/lib/python/
```

# 4. How to Run the Sample

## 4.1. Docker containers


In order to have access to the InterSystems images, we need to go to the following url: http://container.intersystems.com. After connecting with our InterSystems credentials, we will get our password to connect to the registry. In the docker VScode addon, in the image tab, by pressing connect registry and entering the same url as before (http://container.intersystems.com) as a generic registry, we will be asked to give our credentials. The login is the usual one but the password is the one we got from the website.

From there, we should be able to build and compose our containers (with the `docker-compose.yml` and `Dockerfile` files given).

## 4.2. Management Portal and VSCode

This repository is ready for [VS Code](https://code.visualstudio.com/).

Open the locally-cloned `interoperability-embedeed-python` folder in VS Code.

If prompted (bottom right corner), install the recommended extensions.

**IMPORTANT**: When prompted, reopen the folder inside the container so you will be able to use the python components within it. The first time you do this it may take several minutes while the container is readied.

By opening the folder remote you enable VS Code and any terminals you open within it to use the python components within the container. Configure these to use `/usr/irissys/bin/irispython`

<img width="1614" alt="PythonInterpreter" src="https://user-images.githubusercontent.com/47849411/145864423-2de24aaa-036c-4beb-bda0-3a73fe15ccbd.png">

## 4.3. Open the production
To open the production you can go to [production](http://localhost:52773/csp/irisapp/EnsPortal.ProductionConfig.zen?PRODUCTION=PEX.Production).<br>
You can also click on the bottom on the `127.0.0.1:52773[IRISAPP]` button and select `Open Management Portal` then, click on [Interoperability] and [Configure] menus then click [productions] and [Go].

The production already has some code sample.

Here we can see the production and our pure python services and operations:
<img width="1177" alt="interop-screenshot" src="https://user-images.githubusercontent.com/47849411/131305197-d19511fd-6e05-4aec-a525-c88e6ebd0971.png">

<br>

New json trace for python native messages :
<img width="910" alt="json-message-trace" src="https://user-images.githubusercontent.com/47849411/131305211-b8beb2c0-438d-4afc-a6d2-f94d854373ae.png">

# 5. What's inside the repository

## 5.1. Dockerfile

A dockerfile which install some python dependancies (pip, venv) and sudo in the container for conviencies.
Then it create the dev directory and copy in it this git repository.

It starts IRIS and activates **%Service_CallIn** for **Python Shell**.
Use the related docker-compose.yml to easily setup additional parametes like port number and where you map keys and host folders.

This dockerfile ends with the installation of requirements for python modules.

Use .env/ file to adjust the dockerfile being used in docker-compose.

## 5.2. .vscode/settings.json

Settings file to let you immedietly code in VSCode with [VSCode ObjectScript plugin](https://marketplace.visualstudio.com/items?itemName=daimor.vscode-objectscript)

## 5.3. .vscode/launch.json
Config file if you want to debug with VSCode ObjectScript

[Read about all the files in this article](https://community.intersystems.com/post/dockerfile-and-friends-or-how-run-and-collaborate-objectscript-projects-intersystems-iris)

## 5.4. .vscode/extensions.json
Recommendation file to add extensions if you want to run with VSCode in the container.

[More information here](https://code.visualstudio.com/docs/remote/containers)

This is very useful to work with embedded python.

## 5.5. src folder

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
│       └── _utils.cls
├── PEX // Some example of wrapped classes
│   └── Production.cls
└── python
    ├── demo // Actual python code to run this demo
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
    │       ├── _business_host.py
    │       ├── _business_operation.py
    │       ├── _business_process.py
    │       ├── _business_service.py
    │       ├── _common.py
    │       ├── _director.py
    │       ├── _inbound_adapter.py
    │       ├── _message.py
    │       ├── _outbound_adapter.py
    │       ├── __init__.py
    │       └── _utils.py
    └── setup.py // setup to build the wheel
```
# 6. How it works

## 6.1. The `__init__.py`file
This file will allow us to create the classes to import in the code.<br>
It gets from the multiple files seen earlier the classes and make them into callable classes.
That way, when you wish to create a business operation, for example, you can just do:
```python
from iop import BusinessOperation
```

## 6.2. The `common` class
The common class shouldn't be called by the user, it defines almost all the other classes.<br>
This class defines:

`on_init`: The on_init() method is called when the component is started.<br> Use the on_init() method to initialize any structures needed by the component.

`on_tear_down`: Called before the component is terminated.<br> Use it to free any structures.

`on_connected`: The on_connected() method is called when the component is connected or reconnected after being disconnected.<br>Use the on_connected() method to initialize any structures needed by the component.

`log_info`: Write a log entry of type "info". :log entries can be viewed in the management portal.

`log_alert`: Write a log entry of type "alert". :log entries can be viewed in the management portal.

`log_warning`: Write a log entry of type "warning". :log entries can be viewed in the management portal.

`log_error`: Write a log entry of type "error". :log entries can be viewed in the management portal.

## 6.3. The `business_host` class
The business host class shouldn't be called by the user, it is the base class for all the business classes.<br>
This class defines:

`send_request_sync`: Send the specified message to the target business process or business operation synchronously.            
**Parameters**:<br>
- **target**: a string that specifies the name of the business process or operation to receive the request. <br>
    The target is the name of the component as specified in the Item Name property in the production definition, not the class name of the component.
- **request**: specifies the message to send to the target. The request is either an instance of a class that is a subclass of Message class or of IRISObject class.<br>
    If the target is a build-in ObjectScript component, you should use the IRISObject class. The IRISObject class enables the PEX framework to convert the message to a class supported by the target.
- **timeout**: an optional integer that specifies the number of seconds to wait before treating the send request as a failure. The default value is -1, which means wait forever.<br>
description: an optional string parameter that sets a description property in the message header. The default is None.

**Returns**:
    the response object from target.

**Raises**:
TypeError: if request is not of type Message or IRISObject.

<br><br>

`send_request_async`: Send the specified message to the target business process or business operation asynchronously.
**Parameters**:<br>
- **target**: a string that specifies the name of the business process or operation to receive the request. <br>
    The target is the name of the component as specified in the Item Name property in the production definition, not the class name of the component.
- **request**: specifies the message to send to the target. The request is an instance of IRISObject or of a subclass of Message.<br>
    If the target is a built-in ObjectScript component, you should use the IRISObject class. The IRISObject class enables the PEX framework to convert the message to a class supported by the target.
- **description**: an optional string parameter that sets a description property in the message header. The default is None.

**Raises**:
TypeError: if request is not of type Message or IRISObject.

<br><br>

`get_adapter_type`: Name of the registred Adapter.


## 6.4. The `inbound_adapter` class
Inbound Adapter in Python are subclass from iop.InboundAdapter in Python, that inherit from all the functions of the [common class](#72-the-common-class).<br>
This class is responsible for receiving the data from the external system, validating the data, and sending it to the business service by calling the BusinessHost process_input method.
This class defines:

`on_task`: Called by the production framework at intervals determined by the business service CallInterval property.<br>
The message can have any structure agreed upon by the inbound adapter and the business service.

Example of an inbound adapter ( situated in the src/python/demo/reddit/adapter.py file ):
```python
from iop import InboundAdapter
import requests
import iris
import json

class RedditInboundAdapter(InboundAdapter):
    """
    This adapter use requests to fetch self.limit posts as data from the reddit
    API before calling process_input for each post.
    """
    def on_init(self):
        
        if not hasattr(self,'feed'):
            self.feed = "/new/"
        
        if self.limit is None:
            raise TypeError('no Limit field')
        
        self.last_post_name = ""
        
        return 1

    def on_task(self):
        self.log_info(f"LIMIT:{self.limit}")
        if self.feed == "" :
            return 1
        
        tSC = 1
        # HTTP Request
        try:
            server = "https://www.reddit.com"
            request_string = self.feed+".json?before="+self.last_post_name+"&limit="+self.limit
            self.log_info(server+request_string)
            response = requests.get(server+request_string)
            response.raise_for_status()

            data = response.json()
            updateLast = 0

            for key, value in enumerate(data['data']['children']):
                if value['data']['selftext']=="":
                    continue
                post = iris.cls('dc.Reddit.Post')._New()
                post._JSONImport(json.dumps(value['data']))
                post.OriginalJSON = json.dumps(value)
                if not updateLast:
                    self.LastPostName = value['data']['name']
                    updateLast = 1
                response = self.BusinessHost.ProcessInput(post)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 429:
                self.log_warning(err.__str__())
            else:
                raise err
        except Exception as err: 
            self.log_error(err.__str__())
            raise err

        return tSC
```

## 6.5. The `outbound_adapter` class
Outbound Adapter in Python are subclass from iop.OutboundAdapter in Python, that inherit from all the functions of the [common class](#72-the-common-class).<br>
This class is responsible for sending the data to the external system.

The Outbound Adapter gives the Operation the possibility to have a heartbeat notion.
To activate this option, the CallInterval parameter of the adapter must be strictly greater than 0.

<img width="301" alt="image" src="https://user-images.githubusercontent.com/47849411/178230243-39806602-a63d-4a89-9563-fcf6836d0515.png">

Example of an outbound adapter ( situated in the src/python/demo/reddit/adapter.py file ):

```python
class TestHeartBeat(OutboundAdapter):

    def on_keepalive(self):
        self.log_info('beep')

    def on_task(self):
        self.log_info('on_task')
```

## 6.6. The `business_service` class
This class is responsible for receiving the data from external system and sending it to business processes or business operations in the production.<br>
The business service can use an adapter to access the external system, which is specified overriding the get_adapter_type method.<br>
There are three ways of implementing a business service:<br>
- Polling business service with an adapter - The production framework at regular intervals calls the adapter’s OnTask() method, 
    which sends the incoming data to the the business service ProcessInput() method, which, in turn calls the OnProcessInput method with your code.

- Polling business service that uses the default adapter - In this case, the framework calls the default adapter's OnTask method with no data. 
    The OnProcessInput() method then performs the role of the adapter and is responsible for accessing the external system and receiving the data.

- Nonpolling business service - The production framework does not initiate the business service. Instead custom code in either a long-running process 
    or one that is started at regular intervals initiates the business service by calling the Director.CreateBusinessService() method.

Business service in Python are subclass from iop.BusinessService in Python, that inherit from all the functions of the [business host](#73-the-business_host-class).<br>
This class defines:

`on_process_input`: Receives the message from the inbond adapter via the PRocessInput method and is responsible for forwarding it to target business processes or operations.<br>
If the business service does not specify an adapter, then the default adapter calls this method with no message and the business service is responsible for receiving the data from the external system and validating it.
**Parameters**:<br>
- **message_input**: an instance of IRISObject or subclass of Message containing the data that the inbound adapter passes in.<br>
The message can have any structure agreed upon by the inbound adapter and the business service. 

<br><br>

Example of a business service ( situated in the src/python/demo/reddit/bs.py file ):
```python
from iop import BusinessService

import iris

from message import PostMessage
from obj import PostClass

class RedditServiceWithPexAdapter(BusinessService):
    """
    This service use our python Python.RedditInboundAdapter to receive post
    from reddit and call the FilterPostRoutingRule process.
    """
    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return "Python.RedditInboundAdapter"

    def on_process_input(self, message_input):
        msg = iris.cls("dc.Demo.PostMessage")._New()
        msg.Post = message_input
        return self.send_request_sync(self.target,msg)

    def on_init(self):
        
        if not hasattr(self,'target'):
            self.target = "Python.FilterPostRoutingRule"
        
        return
```


## 6.7. The `business_process` class
Typically contains most of the logic in a production.<br>
A business process can receive messages from a business service, another business process, or a business operation.<br>
It can modify the message, convert it to a different format, or route it based on the message contents.<br>
The business process can route a message to a business operation or another business process.<br>
Business processes in Python are subclass from iop.BusinessProcess in Python, that inherit from all the functions of the [business host](#73-the-business_host-class).<br>
This class defines:

`on_request`: Handles requests sent to the business process. A production calls this method whenever an initial request for a specific business process arrives on the appropriate queue and is assigned a job in which to execute.<br>
**Parameters**:<br>
- **request**: An instance of IRISObject or subclass of Message that contains the request message sent to the business process.

**Returns**:
An instance of IRISObject or subclass of Message that contains the response message that this business process can return
to the production component that sent the initial message.

<br><br>

`on_response`: Handles responses sent to the business process in response to messages that it sent to the target.<br>
A production calls this method whenever a response for a specific business process arrives on the appropriate queue and is assigned a job in which to execute.<br>
Typically this is a response to an asynchronous request made by the business process where the responseRequired parameter has a true value.<br>
**Parameters**:<br>
- **request**: An instance of IRISObject or subclass of Message that contains the initial request message sent to the business process.
- **response**: An instance of IRISObject or subclass of Message that contains the response message that this business process can return to the production component that sent the initial message.
- **callRequest**: An instance of IRISObject or subclass of Message that contains the request that the business process sent to its target.
- **callResponse**: An instance of IRISObject or subclass of Message that contains the incoming response.
- **completionKey**: A string that contains the completionKey specified in the completionKey parameter of the outgoing SendAsync() method.

**Returns**:
An instance of IRISObject or subclass of Message that contains the response message that this business process can return
to the production component that sent the initial message.

<br><br>

`on_complete`: Called after the business process has received and handled all responses to requests it has sent to targets.<br>
**Parameters**: 
- **request**: An instance of IRISObject or subclass of Message that contains the initial request message sent to the business process.<br>
- **response**: An instance of IRISObject or subclass of Message that contains the response message that this business process can return to the production component that sent the initial message.

**Returns**:
An instance of IRISObject or subclass of Message that contains the response message that this business process can return to the production component that sent the initial message.

<br><br>

Example of a business process ( situated in the src/python/demo/reddit/bp.py file ):
```python
from iop import BusinessProcess

from message import PostMessage
from obj import PostClass

class FilterPostRoutingRule(BusinessProcess):
    """
    This process receive a PostMessage containing a reddit post.
    It then understand if the post is about a dog or a cat or nothing and
    fill the right infomation inside the PostMessage before sending it to
    the FileOperation operation.
    """
    def on_init(self):
        
        if not hasattr(self,'target'):
            self.target = "Python.FileOperation"
        
        return

    def on_request(self, request):

        if 'dog'.upper() in request.post.selftext.upper():
            request.to_email_address = 'dog@company.com'
            request.found = 'Dog'
        if 'cat'.upper() in request.post.selftext.upper():
            request.to_email_address = 'cat@company.com'
            request.found = 'Cat'

        if request.found is not None:
            return self.send_request_sync(self.target,request)
        else:
            return
```

## 6.8. The `business_operation` class
This class is responsible for sending the data to an external system or a local system such as an iris database.<br>
The business operation can optionally use an adapter to handle the outgoing message which is specified overriding the get_adapter_type method.<br>
If the business operation has an adapter, it uses the adapter to send the message to the external system.<br>
The adapter can either be a PEX adapter, an ObjectScript adapter or a [python adapter](#75-the-outbound_adapter-class).<br>
Business operation in Python are subclass from iop.BusinessOperation in Python, that inherit from all the functions of the [business host](#73-the-business_host-class).<br>

### 6.8.1. The dispacth system
In a business operation it is possbile to create any number of function [similar to the on_message method](#782-the-methods) that will take as argument a [typed request](#711-the-messages) like this `my_special_message_method(self,request: MySpecialMessage)`.

The dispatch system will automatically analyze any request arriving to the operation and dispacth the requests depending of their type. If the type of the request is not recognized or is not specified in any **on_message like function**, the dispatch system will send it to the `on_message` function.

### 6.8.2. The methods
This class defines:

`on_message`: Called when the business operation receives a message from another production component [that can not be dispatched to another function](#781-the-dispacth-system).<br>
Typically, the operation will either send the message to the external system or forward it to a business process or another business operation.
If the operation has an adapter, it uses the Adapter.invoke() method to call the method on the adapter that sends the message to the external system.
If the operation is forwarding the message to another production component, it uses the SendRequestAsync() or the SendRequestSync() method.<br>
**Parameters**:
- **request**: An instance of either a subclass of Message or of IRISObject containing the incoming message for the business operation.

**Returns**:
The response object

Example of a business operation ( situated in the src/python/demo/reddit/bo.py file ):
```python
from iop import BusinessOperation

from message import MyRequest,MyMessage

import iris

import os
import datetime
import smtplib
from email.mime.text import MIMEText

class EmailOperation(BusinessOperation):
    """
    This operation receive a PostMessage and send an email with all the
    important information to the concerned company ( dog or cat company )
    """

    def my_message(self,request:MyMessage):
        sender = 'admin@example.com'
        receivers = 'toto@example.com'
        port = 1025
        msg = MIMEText(request.toto)

        msg['Subject'] = 'MyMessage'
        msg['From'] = sender
        msg['To'] = receivers

        with smtplib.SMTP('localhost', port) as server:
            server.sendmail(sender, receivers, msg.as_string())
            print("Successfully sent email")

    def on_message(self, request):

        sender = 'admin@example.com'
        receivers = [ request.to_email_address ]


        port = 1025
        msg = MIMEText('This is test mail')

        msg['Subject'] = request.found+" found"
        msg['From'] = 'admin@example.com'
        msg['To'] = request.to_email_address

        with smtplib.SMTP('localhost', port) as server:
            
            # server.login('username', 'password')
            server.sendmail(sender, receivers, msg.as_string())
            print("Successfully sent email")

```
If this operation is called using a MyRequest message, the my_message function will be called thanks to the dispatcher, otherwise the on_message function will be called.

## 6.9. The `director` class
The Director class is used for nonpolling business services, that is, business services which are not automatically called by the production framework (through the inbound adapter) at the call interval.<br>
Instead these business services are created by a custom application by calling the Director.create_business_service() method.<br>
This class defines:

`create_business_service`: The create_business_service() method initiates the specified business service.<br>
**Parameters**:
- **connection**: an IRISConnection object that specifies the connection to an IRIS instance for Java.
- **target**: a string that specifies the name of the business service in the production definition.

**Returns**:
an object that contains an instance of IRISBusinessService

`start_production`: The start_production() method starts the production.<br>
**Parameters**:
- **production_name**: a string that specifies the name of the production to start.

`stop_production`: The stop_production() method stops the production.<br>
**Parameters**:
- **production_name**: a string that specifies the name of the production to stop.

`restart_production`: The restart_production() method restarts the production.<br>
**Parameters**:
- **production_name**: a string that specifies the name of the production to restart.

`list_productions`: The list_productions() method returns a dictionary of the names of the productions that are currently running.<br>

## 6.10. The `objects`
We will use `dataclass` to hold information in our [messages](#711-the-messages) in a `obj.py` file.

Example of an object ( situated in the src/python/demo/reddit/obj.py file ):
```python
from dataclasses import dataclass

@dataclass
class PostClass:
    title: str
    selftext : str
    author: str
    url: str
    created_utc: float = None
    original_json: str = None
```

## 6.11. The `messages`
The messages will contain one or more [objects](#710-the-objects), located in the `obj.py` file.<br>
Messages, requests and responses all inherit from the `iop.Message` class.

These messages will allow us to transfer information between any business service/process/operation.

Example of a message ( situated in the src/python/demo/reddit/message.py file ):
```python
from iop import Message

from dataclasses import dataclass

from obj import PostClass

@dataclass
class PostMessage(Message):
    post:PostClass = None
    to_email_address:str = None
    found:str = None
```

WIP It is to be noted that it is needed to use types when you define an object or a message.

## 6.12. How to regsiter a component 

You can register a component to iris in many way :
* Only one component with `register_component` 
* All the component in a file with `register_file` 
* All the component in a folder with `register_folder` 

### 6.12.1. register_component

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.

```python
from iop import Utils
Utils.register_component(<ModuleName>,<ClassName>,<PathToPyFile>,<OverWrite>,<NameOfTheComponent>)
```

e.g :
```python
from iop import Utils
Utils.register_component("MyCombinedBusinessOperation","MyCombinedBusinessOperation","/irisdev/app/src/python/demo/",1,"PEX.MyCombinedBusinessOperation")
```

### 6.12.2. register_file

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.

```python
from iop import Utils
Utils.register_file(<File>,<OverWrite>,<PackageName>)
```

e.g :
```python
from iop import Utils
Utils.register_file("/irisdev/app/src/python/demo/bo.py",1,"PEX")
```

### 6.12.3. register_folder

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this class method to add a new py file to the component list for interoperability.

```python
from iop import Utils
Utils.register_folder(<Path>,<OverWrite>,<PackageName>)
```

e.g :
```python
from iop import Utils
Utils.register_folder("/irisdev/app/src/python/demo/",1,"PEX")
```

### 6.12.4. migrate

Start an embedded python shell :

```sh
/usr/irissys/bin/irispython
```

Then use this static method to migrate the settings file to the iris framework.

```python
from iop import Utils
Utils.migrate()
```

#### 6.12.4.1. setting.py file

This file is used to store the settings of the interoperability components.

It has two sections :
* `CLASSES` : This section is used to store the classes of the interoperability components.
* `PRODUCTIONS` : This section is used to store the productions of the interoperability components.

e.g :
```python
import bp
from bo import *
from bs import *

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.FileOperation': FileOperation,
    'Python.FileOperationWithIrisAdapter': FileOperationWithIrisAdapter,
}

PRODUCTIONS = [
    {
        'dc.Python.Production': {
        "@Name": "dc.Demo.Production",
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
                "Setting": {
                    "@Target": "Host",
                    "@Name": "%settings",
                    "#text": "path=/tmp"
                }
            },
            {
                "@Name": "Python.RedditService",
                "@Category": "",
                "@ClassName": "Python.RedditService",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": "",
                "Setting": [
                    {
                        "@Target": "Host",
                        "@Name": "%settings",
                        "#text": "limit=10\nother<10"
                    }
                ]
            },
            {
                "@Name": "Python.FilterPostRoutingRule",
                "@Category": "",
                "@ClassName": "Python.FilterPostRoutingRule",
                "@PoolSize": "1",
                "@Enabled": "true",
                "@Foreground": "false",
                "@Comment": "",
                "@LogTraceEvents": "false",
                "@Schedule": ""
            }
        ]
    }
    }
]
```

##### 6.12.4.1.1. CLASSES section

This section is used to store the classes of the interoperability components.

It aims to help to register the components.

This dictionary has the following structure :
* Key : The name of the component
* Value : 
  * The class of the component (you have to import it before)
  * The module of the component (you have to import it before)
  * Another dictionary with the following structure :
    * `module` : Name of the module of the component (optional)
    * `class` : Name of the class of the component (optional)
    * `path` : The path of the component (mandatory)

e.g :

When Value is a class or a module:
```python
import bo
import bp
from bs import RedditService

CLASSES = {
    'Python.RedditService': RedditService,
    'Python.FilterPostRoutingRule': bp.FilterPostRoutingRule,
    'Python.FileOperation': bo,
}
```

When Value is a dictionary :
```python
CLASSES = {
    'Python.RedditService': {
        'module': 'bs',
        'class': 'RedditService',
        'path': '/irisdev/app/src/python/demo/'
    },
    'Python.Module': {
        'module': 'bp',
        'path': '/irisdev/app/src/python/demo/'
    },
    'Python.Package': {
        'path': '/irisdev/app/src/python/demo/'
    },
}
```

##### 6.12.4.1.2. Productions section

This section is used to store the productions of the interoperability components.

It aims to help to register a production.

This list has the following structure :
* A list of dictionary with the following structure :
  * `dc.Python.Production` : The name of the production
    * `@Name` : The name of the production
    * `@TestingEnabled` : The testing enabled of the production
    * `@LogGeneralTraceEvents` : The log general trace events of the production
    * `Description` : The description of the production
    * `ActorPoolSize` : The actor pool size of the production
    * `Item` : The list of the items of the production
      * `@Name` : The name of the item
      * `@Category` : The category of the item
      * `@ClassName` : The class name of the item
      * `@PoolSize` : The pool size of the item
      * `@Enabled` : The enabled of the item
      * `@Foreground` : The foreground of the item
      * `@Comment` : The comment of the item
      * `@LogTraceEvents` : The log trace events of the item
      * `@Schedule` : The schedule of the item
      * `Setting` : The list of the settings of the item
        * `@Target` : The target of the setting
        * `@Name` : The name of the setting
        * `#text` : The value of the setting

The minimum structure of a production is :
```python
PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Python.FileOperation",
                    },
                    {
                        "@Name": "Python.EmailOperation",
                        "@ClassName": "UnitTest.Package.EmailOperation"
                    }
                ]
            }
        } 
    ]
```

You can also set in `@ClassName` an item from the CLASSES section.

e.g :
```python
from bo import FileOperation
PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": FileOperation,
                    }
                ]
            }
        } 
    ]
```

As the production is a dictionary, you can add in value of the production dictionary an environment variable.

e.g :
```python
import os

PRODUCTIONS = [
        {
            'UnitTest.Production': {
                "Item": [
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Python.FileOperation",
                        "Setting": {
                            "@Target": "Host",
                            "@Name": "%settings",
                            "#text": os.environ['SETTINGS']
                        }
                    }
                ]
            }
        } 
    ]
```

## 6.13. Direct use of IOP

If you don't want to use the register_component util. You can add a IOP.BusinessService component directly into the management portal and configure the properties :
- %module :
  - Module name of your python code
- %classname :
  - Classname of you component
- %classpaths
  - Path where you component is.
    - This can one or more Classpaths (separated by '|' character) needed in addition to PYTHON_PATH

e.g :
<img width="800" alt="component-config" src="https://user-images.githubusercontent.com/47849411/131316308-e1898b19-11df-433b-b1c6-7f69d5cc9974.png">

# 7. Command line

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

## 7.1. help

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

## 7.2. default

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

## 7.3. lists

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

## 7.4. start

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

## 7.5. kill

The kill command kill a production (force stop).

Kill command is the same as stop command but with a force stop.

Kill command doesn't take an argument because only one production can be running.

```bash
iop -k 
```

## 7.6. stop

The stop command stop a production.

Stop command doesn't take an argument because only one production can be running.

```bash
iop -S 
```

## 7.7. restart

The restart command restart a production.

Restart command doesn't take an argument because only one production can be running.

```bash
iop -r 
```

## 7.8. migrate

The migrate command migrate a production and classes with settings file.

Migrate command must take the absolute path of the settings file.

Settings file must be in the same folder as the python code.

```bash
iop -M /tmp/settings.py
```

## 7.9. export

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

## 7.10. status

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

## 7.11. version

The version command display the version.

```bash
iop -v
```

output :
```bash
2.3.0
```

## 7.12. log

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

# 8. Credits

Most of the code came from PEX for Python by Mo Cheng and Summer Gerry.

Works only on IRIS 2021.2 +