import iris

from iop._utils import _Utils

def test_register_message_schema():
    from registerFilesIop.message import SimpleMessage
    _Utils.register_message_schema(SimpleMessage)

    iop_schema_name = SimpleMessage.__module__ + '.' + SimpleMessage.__name__
    iop_schema = iris.cls('IOP.Message.JSONSchema')._OpenId(iop_schema_name)
    assert iop_schema is not None
    assert iop_schema.Category == iop_schema_name
    assert iop_schema.Name == iop_schema_name
    