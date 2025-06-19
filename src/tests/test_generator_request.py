import pytest
from iop._generator_request import _GeneratorRequest
from iop import PydanticMessage
from unittest.mock import Mock, patch

def test_generator_request_initialization():
    # Mock host and request
    mock_host = Mock()
    mock_request = PydanticMessage()
    
    # Set up mock response for send_request_sync
    mock_ack = Mock()
    mock_ack._IsA.return_value = True
    mock_host.send_request_sync.return_value = mock_ack
    
    # Test successful initialization
    generator = _GeneratorRequest(mock_host, "test_target", mock_request)
    assert generator.host == mock_host
    assert generator.target == "test_target"
    assert generator.request == mock_request
    
    # Verify send_request_sync was called correctly
    mock_host.send_request_sync.assert_called_once()

def test_generator_request_failed_initialization():
    # Mock host and request
    mock_host = Mock()
    mock_request = PydanticMessage()
    
    # Set up mock response for send_request_sync to fail
    mock_host.send_request_sync.return_value = None
    
    # Test failed initialization
    with pytest.raises(RuntimeError, match="Failed to send request, no acknowledgment received."):
        _GeneratorRequest(mock_host, "test_target", mock_request)

def test_generator_request_iteration():
    # Mock host and request
    mock_host = Mock()
    mock_request = PydanticMessage()
    
    # Set up mock responses for all calls: initialization, iteration, and stop
    mock_ack = Mock()
    mock_ack._IsA.return_value = True
    mock_response = Mock()
    mock_response._IsA.return_value = False
    mock_stop = Mock()
    mock_stop._IsA.return_value = True
    
    # Configure mock to return ack for init, regular response, then stop message
    mock_host.send_request_sync.side_effect = [mock_ack, mock_response, mock_stop]
    
    # Create generator
    generator = _GeneratorRequest(mock_host, "test_target", mock_request)
    
    # Test iteration
    responses = list(generator)
    assert len(responses) == 1
    assert responses[0] == mock_response

def test_generator_request_none_response():
    # Mock host and request
    mock_host = Mock()
    mock_request = PydanticMessage()
    
    # Set up mock response for initialization
    mock_ack = Mock()
    mock_ack._IsA.return_value = True
    mock_host.send_request_sync.return_value = mock_ack
    
    # Create generator
    generator = _GeneratorRequest(mock_host, "test_target", mock_request)
    
    # Set up mock to return None for iteration
    mock_host.send_request_sync.side_effect = [None]
    
    # Test iteration should stop on None response
    responses = list(generator)
    assert len(responses) == 0