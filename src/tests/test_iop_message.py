import iris

def test_iop_message_set_json():
    # test set_json
    iop_message = iris.cls('IOP.Message')._New()
    iop_message.json = 'test'
    assert iop_message.jstr.Read() == 'test'
    assert iop_message.type == 'String'
    assert iop_message.jsonString == 'test'
    assert iop_message.json == 'test'