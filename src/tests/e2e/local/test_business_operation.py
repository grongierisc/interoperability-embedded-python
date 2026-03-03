"""E2E (local IRIS) tests for _BusinessOperation."""
import iris
import pytest
from unittest.mock import MagicMock

from iop._business_operation import _BusinessOperation
from iop._dispatch import dispatch_serializer
from fixtures.message import SimpleMessage


def test_dispatch_on_message():
    class CustomOperation(_BusinessOperation):
        def handle_simple(self, request: SimpleMessage):
            return SimpleMessage(integer=request.integer + 1, string="handled")

    request = iris.cls("IOP.Message")._New()
    request.json = '{"integer": 1, "string": "test"}'
    request.classname = 'fixtures.message.SimpleMessage'

    operation = CustomOperation()
    mock_host = MagicMock()
    mock_host.port = 0
    mock_host.enable = False
    operation._dispatch_on_init(mock_host)

    response = operation._dispatch_on_message(request)
    expected_response = dispatch_serializer(SimpleMessage(integer=2, string='handled'))

    assert response.json == expected_response.json
