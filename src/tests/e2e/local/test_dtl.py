import json
import os

import iris
import pytest
from fixtures.message import ComplexMessage, SimpleMessage, TaskMessage

from iop.migration import utils as migration_utils

# Constants
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "cls")


# Fixtures
@pytest.fixture
def load_cls_files():
    migration_utils.raise_on_error(
        iris.cls("%SYSTEM.OBJ").LoadDir(TEST_DATA_DIR, "uk", "*.cls", 1)
    )
    migration_utils.raise_on_error(iris.cls("%SYSTEM.OBJ").Compile("UnitTest.*", "cb"))


@pytest.fixture
def iop_message():
    return iris.cls("IOP.Message")._New()


# Test Data
GET_VALUE_TEST_CASES = [
    ('{"string":"Foo", "integer":42}', "string", "Foo"),
    (
        '{"post":{"Title":"Foo"}, "string":"bar", "list_str":["Foo","Bar"]}',
        "post.Title",
        "Foo",
    ),
    (
        '{"post":{"Title":"Foo"}, "list_post":[{"Title":"Bar"},{"Title":"Foo"}]}',
        "list_post(2).Title",
        "Foo",
    ),
    ('{"list_str":["Foo","Bar"]}', "list_str(2)", "Bar"),
    ('{"list_str":["Foo","Bar"]}', "list_str()", ["Foo", "Bar"]),
    ('{"list_str":["Foo","Bar"]}', "list_str", ["Foo", "Bar"]),
    ('{"list":["Foo",["Bar","Baz"]]}', "list(2)(2)", "Baz"),
]

SET_VALUE_TEST_CASES = [
    (
        '{"string":"Foo", "integer":42}',
        "string",
        "Bar",
        "set",
        None,
        '{"string":"Bar", "integer":42}',
    ),
    (
        r'{"post":{"Title":"Foo"}}',
        "post.Title",
        "Bar",
        "set",
        None,
        r'{"post":{"Title":"Bar"}}',
    ),
    (r"{}", "post.Title", "Bar", "set", None, r'{"post":{"Title":"Bar"}}'),
    (r"{}", "post()", "Bar", "append", None, r'{"post":["Bar"]}'),
    (r'{"post":["Foo"]}', "post()", "Bar", "append", None, r'{"post":["Foo","Bar"]}'),
]

TRANSFORM_TEST_CASES = [
    (
        '{"string":"Foo", "integer":42}',
        "fixtures.message.SimpleMessage",
        "UnitTest.SimpleMessageGet",
        "Foo",
    ),
    (
        '{"post":{"Title":"Foo"}, "string":"bar", "list_str":["Foo","Bar"]}',
        "fixtures.message.ComplexMessage",
        "UnitTest.ComplexGet",
        "Foo",
    ),
    (
        '{"post":{"Title":"Foo"}, "list_post":[{"Title":"Bar"},{"Title":"Foo"}]}',
        "fixtures.message.ComplexMessage",
        "UnitTest.ComplexGetList",
        "Foo",
    ),
]


# Tests
class TestMessageSchema:
    @pytest.mark.parametrize(
        "message_class,expected_name",
        [
            (SimpleMessage, f"{SimpleMessage.__module__}.{SimpleMessage.__name__}"),
            (ComplexMessage, f"{ComplexMessage.__module__}.{ComplexMessage.__name__}"),
        ],
    )
    def test_register_message_schema(self, message_class, expected_name):
        migration_utils.register_message_schema(message_class)
        iop_schema = iris.cls("IOP.Message.JSONSchema")._OpenId(expected_name)
        assert iop_schema is not None
        assert iop_schema.Category == expected_name
        assert iop_schema.Name == expected_name


class TestMessageOperations:
    @pytest.mark.parametrize("json_data,path,expected", GET_VALUE_TEST_CASES)
    def test_get_value_at(self, iop_message, json_data, path, expected):
        iop_message.json = json_data
        result = iop_message.GetValueAt(path)
        assert result == expected

    @pytest.mark.parametrize(
        "json_data,path,value,action,key,expected_json", SET_VALUE_TEST_CASES
    )
    def test_set_value_at(
        self, iop_message, json_data, path, value, action, key, expected_json
    ):
        iop_message.json = json_data
        iop_message.classname = "foo"
        migration_utils.raise_on_error(iop_message.SetValueAt(value, path, action, key))
        assert json.loads(iop_message.json) == json.loads(expected_json)


class TestTransformations:
    @pytest.mark.parametrize(
        "json_data,classname,transform_class,expected_value", TRANSFORM_TEST_CASES
    )
    def test_get_transform(
        self,
        load_cls_files,
        iop_message,
        json_data,
        classname,
        transform_class,
        expected_value,
    ):
        ref = iris.ref(None)
        iop_message.json = json_data
        iop_message.classname = classname

        iris.cls(transform_class).Transform(iop_message, ref)
        result = ref.value

        assert result.StringValue == expected_value

    def test_set_transform(self, load_cls_files):
        ref = iris.ref(None)
        message = iris.cls("Ens.StringRequest")._New()
        message.StringValue = "Foo"

        migration_utils.raise_on_error(
            iris.cls("UnitTest.SimpleMessageSet").Transform(message, ref)
        )
        result = ref.value

        assert json.loads(result.json) == json.loads('{"string":"Foo"}')

    def test_set_transform_vdoc(self, load_cls_files, iop_message):
        ref = iris.ref(None)
        iop_message.json = '{"string":"Foo", "integer":42}'
        iop_message.classname = "fixtures.message.SimpleMessage"

        migration_utils.raise_on_error(
            iris.cls("UnitTest.SimpleMessageSetVDoc").Transform(iop_message, ref)
        )
        result = ref.value

        assert json.loads(result.json) == json.loads('{"string":"Foo", "integer":42}')
        assert result.classname == "fixtures.message.SimpleMessage"


class TestEnumSchemaHandling:
    """Test that enums are properly handled in JSON schema to contents conversion."""

    def test_enum_schema_to_contents(self):
        """Test that enum types are properly converted to contents format."""
        # Register TaskMessage schema
        migration_utils.register_message_schema(TaskMessage)

        # Get the schema from storage
        schema_name = f"{TaskMessage.__module__}.{TaskMessage.__name__}"
        iop_schema = iris.cls("IOP.Message.JSONSchema")._OpenId(schema_name)
        assert iop_schema is not None

        # Parse the schema
        schema = json.loads(iop_schema.JSONSchema)

        # Verify schema has definitions for enums
        assert "$defs" in schema
        assert "Status" in schema["$defs"]
        assert "Priority" in schema["$defs"]

        # Verify enum definition structure
        status_enum = schema["$defs"]["Status"]
        assert status_enum["type"] == "string"
        assert "enum" in status_enum
        assert set(status_enum["enum"]) == {"ACTIVE", "INACTIVE", "PENDING"}

        priority_enum = schema["$defs"]["Priority"]
        assert priority_enum["type"] == "string"
        assert "enum" in priority_enum
        assert set(priority_enum["enum"]) == {"HIGH", "MEDIUM", "LOW"}

    def test_schema_to_contents_with_enum(self):
        """Test SchemaToContents correctly processes enum definitions."""
        # Register TaskMessage schema
        migration_utils.register_message_schema(TaskMessage)

        # Get schema
        schema_name = f"{TaskMessage.__module__}.{TaskMessage.__name__}"
        iop_schema = iris.cls("IOP.Message.JSONSchema")._OpenId(schema_name)
        schema_json = iop_schema.JSONSchema
        schema = iris.cls("%DynamicObject")._FromJSON(schema_json)

        # Convert schema to contents
        contents = iris.ref(None)
        migration_utils.raise_on_error(
            iris.cls("IOP.Message").SchemaToContents(schema, contents)
        )

        # Verify contents were generated
        result = contents.value
        assert result is not None

    def test_enum_ref_resolution(self):
        """Test that enum references in schema are properly resolved."""
        # Create schema with enum references
        schema_json = """{
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "status": {"$ref": "#/$defs/Status"}
            },
            "$defs": {
                "Status": {
                    "type": "string",
                    "enum": ["ACTIVE", "INACTIVE", "PENDING"],
                    "title": "Status"
                }
            }
        }"""

        schema = iris.cls("%DynamicObject")._FromJSON(schema_json)

        # Convert to contents
        contents = iris.ref(None)
        migration_utils.raise_on_error(
            iris.cls("IOP.Message").SchemaToContents(schema, contents)
        )

        # Verify that contents generated successfully
        result = contents.value
        assert result is not None
