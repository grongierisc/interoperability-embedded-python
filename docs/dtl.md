# DTL Support

Starting with version 3.2.0, IoP supports DTL transformations. 
DTL the Data Transformation Layer in IRIS Interoperability. 
DTL transformations are used to transform data from one format to another with a graphical editor.
It supports also `jsonschema` structures.

## How to use DTL in with Message

First you need to register you message class is a `settings.py` file.

To do so, you need to add the following line in the `settings.py` file:

`settings.py`
```
from msg import MyMessage

SCHEMAS = [MyMessage]
```

Then you can use iop migration command to generate schema files for your message classes.

```bash
iop --migrate /path/to/your/project/settings.py
```

### Example

`msg.py`
```python
from iop import Message
from dataclasses import dataclass

@dataclass
class MyMessage(Message):
    name: str = None
    age: int = None
```

`settings.py`
```python
from msg import MyMessage

SCHEMAS = [MyMessage]
```

Migrate the schema files
```bash
iop --migrate /path/to/your/project/settings.py
```

## Building a DTL Transformation

To build a DTL transformation, you need to create a new DTL transformation class.

Go to the IRIS Interoperability Management Portal and create a new DTL transformation.

![DTL Transformation](./img/interop_dtl_management_portal.png)

Then select the source and target message classes.

![DTL Transformation](./img/dtl_wizard.png)

And it's schema.

![DTL Transformation](./img/vdoc_type.png)

Then you can start building your transformation.

![DTL Transformation](./img/complex_transform.png)

You can even test your transformation.

![DTL Transformation](./img/test_dtl.png)

Example of payload to test as a source message:

```xml
<test>
  <Message>
    <json><![CDATA[
{
"list_str":["toto","titi"],
"post":{"Title":"foo","Selftext":"baz"},
"list_post":[{"Title":"bar","Selftext":"baz"},{"Title":"foo","Selftext":"foo"}]
}
]]></json>
  </Message>
</test>
```

## JsonSchema Support

Starting with version 3.2.0, IoP supports `jsonschema` structures for DTL transformations.

Same as for message classes, you need to register your `jsonschema`.
To do so, you need to invoke his iris command:

```objectscript
zw ##class(IOP.Message.JSONSchema).ImportFromFile("/irisdev/app/random_jsonschema.json","Demo","Demo")
```

Where the first argument is the path to the jsonschema file, the second argument is the package name and the third argument is the name of the schema.

Then you can use it in your DTL transformation.
The schema will be available in the name of `Demo`.