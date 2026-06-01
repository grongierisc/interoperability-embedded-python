import copy
import json
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from iop import (
    BusinessOperation,
    BusinessProcess,
    Message,
    PollingBusinessService,
    Production,
    controls,
    target,
)
from iop._business_host import _BusinessHost
from iop._utils import _Utils


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target("orders")


class OrderOperation(BusinessOperation):
    pass


def _property(component, name):
    return next(prop for prop in component._get_properties() if prop[0] == name)


def test_target_declares_config_name_setting_metadata():
    assert _property(FileService, "Output") == [
        "Output",
        "Ens.DataType.ConfigName",
        "",
        False,
        "Basic",
        "",
        controls.production_item(),
    ]


def test_production_to_dict_with_auto_names_settings_and_connection():
    prod = Production("Demo.Production", testing_enabled=True)
    file = prod.service(
        "FileInput",
        FileService,
        pool_size=2,
        settings={"Limit": 10},
        adapter_settings={"Charset": "utf-8"},
    )
    orders = prod.operation(OrderOperation)

    prod.connect(file.Output, orders)

    data = prod.to_dict()
    production = data["Demo.Production"]
    file_item = production["Item"][0]
    order_item = production["Item"][1]

    assert production["@TestingEnabled"] == "true"
    assert file_item["@Name"] == "FileInput"
    assert file_item["@PoolSize"] == "2"
    assert file_item["@ClassName"] == (
        f"Python.{FileService.__module__}.{FileService.__name__}".replace("_", "")
    )
    assert order_item["@Name"] == "OrderOperation"

    settings = {
        (setting["@Target"], setting["@Name"]): setting["#text"]
        for setting in file_item["Setting"]
    }
    assert settings[("Host", "Limit")] == "10"
    assert settings[("Host", "Output")] == "OrderOperation"
    assert settings[("Adapter", "Charset")] == "utf-8"

    assert prod.edges == (
        {
            "source": "FileInput.Output",
            "source_item": "FileInput",
            "source_port": "Output",
            "logical_name": "orders",
            "target": "OrderOperation",
        },
    )


def test_production_test_resolves_string_port_path_from_object_graph():
    director = MagicMock()
    director.test_component.return_value = "ok"
    prod = Production("Test.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    response = prod.test("FileInput.Output", OrderRequest(order_id="123"))

    assert response == "ok"
    director.test_component.assert_called_once()
    _, kwargs = director.test_component.call_args
    assert director.test_component.call_args.args[0] == "OrderOperation"
    assert kwargs["message"] is None
    assert kwargs["classname"] == f"{OrderRequest.__module__}.OrderRequest"
    assert json.loads(kwargs["body"]) == {"order_id": "123"}


def test_production_test_resolves_port_path_from_export_when_graph_is_empty():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Demo.Production",
        "Status": "running",
    }
    director.export_production.return_value = {
        "Demo.Production": {
            "Item": {
                "@Name": "FileInput",
                "Setting": {
                    "@Target": "Host",
                    "@Name": "Output",
                    "#text": "OrderOperation",
                },
            }
        }
    }
    director.test_component.return_value = "ok"
    prod = Production("Demo.Production", director=director)

    response = prod.test("FileInput.Output", OrderRequest(order_id="123"))

    assert response == "ok"
    director.export_production.assert_called_once_with("Demo.Production")
    director.test_component.assert_called_once()
    assert director.test_component.call_args.args[0] == "OrderOperation"


def test_production_test_reports_existing_stopped_production():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Demo.Production",
        "Status": "stopped",
    }
    director.list_productions.return_value = {
        "Demo.Production": {"Status": "Stopped"}
    }
    prod = Production("Demo.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    with pytest.raises(RuntimeError, match="exists but is not running"):
        prod.test("FileInput.Output", OrderRequest(order_id="123"))

    director.test_component.assert_not_called()


def test_production_start_uses_runtime_start_status():
    director = MagicMock()
    director.start_production.side_effect = RuntimeError(
        "IRIS can run only one production at a time"
    )
    prod = Production("Demo.Production", director=director)

    with pytest.raises(RuntimeError, match="IRIS can run only one production"):
        prod.start()

    director.start_production.assert_called_once_with("Demo.Production")


def test_production_test_reports_another_running_production():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Bench.Production",
        "Status": "running",
    }
    director.list_productions.return_value = {
        "Demo.Production": {"Status": "Stopped"},
        "Bench.Production": {"Status": "Running"},
    }
    prod = Production("Demo.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    with pytest.raises(RuntimeError, match="Stop 'Bench.Production' first"):
        prod.test("FileInput.Output", OrderRequest(order_id="123"))

    director.test_component.assert_not_called()


def test_missing_port_connection_raises_clear_error():
    prod = Production("Test.Production")
    file = prod.service("FileInput", FileService)
    prod.operation(OrderOperation)

    with pytest.raises(ValueError, match="not connected"):
        prod.resolve_target(file.Output)

    with pytest.raises(ValueError, match="not connected"):
        prod.resolve_target("FileInput.Output")


def test_production_from_dict_rebuilds_graph_from_runtime_connections():
    exported = {
        "Demo.Production": {
            "@Name": "Demo.Production",
            "@TestingEnabled": "true",
            "Item": [
                {
                    "@Name": "FileInput",
                    "@ClassName": "EnsLib.File.PassthroughService",
                    "Setting": [
                        {
                            "@Target": "Host",
                            "@Name": "TargetConfigNames",
                            "#text": "OrderOperation",
                        },
                        {
                            "@Target": "Adapter",
                            "@Name": "FilePath",
                            "#text": "/tmp",
                        },
                        {
                            "@Target": "Custom",
                            "@Name": "Preserved",
                            "#text": "yes",
                        },
                    ],
                },
                {
                    "@Name": "OrderOperation",
                    "@ClassName": "EnsLib.File.PassthroughOperation",
                },
            ],
        }
    }
    connections = {
        "production": "Demo.Production",
        "items": [
            {"item": "FileInput", "connections": ["OrderOperation"]},
            {"item": "OrderOperation", "connections": []},
        ],
    }

    prod = Production.from_dict(exported, connections=connections)

    assert prod.item("FileInput").class_name == "EnsLib.File.PassthroughService"
    assert prod.item("FileInput").adapter_settings == {"FilePath": "/tmp"}
    assert prod.item("FileInput").other_settings == [
        {"@Target": "Custom", "@Name": "Preserved", "#text": "yes"}
    ]
    assert prod.item("FileInput").TargetConfigNames.resolve() == "OrderOperation"

    graph = prod.graph()
    assert graph.to_dict()["edges"] == [
        {
            "source": "FileInput.TargetConfigNames",
            "source_item": "FileInput",
            "source_port": "TargetConfigNames",
            "logical_name": "",
            "target": "OrderOperation",
            "runtime": True,
        }
    ]
    assert "FileInput [EnsLib.File.PassthroughService]" in str(graph)
    assert "TargetConfigNames -> OrderOperation" in str(graph)


def test_production_from_dict_keeps_queue_as_runtime_metadata():
    exported = {
        "Demo.Production": {
            "Item": [
                {"@Name": "FileInput", "@ClassName": "Demo.FileService"},
                {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
            ]
        }
    }
    queue_info = {
        "production": "Demo.Production",
        "items": [
            {
                "item": "FileInput",
                "queue_name": "FileInput",
                "count": 3,
                "exists": True,
            }
        ],
    }

    prod = Production.from_dict(exported, queue_info=queue_info)

    assert prod.queue(refresh=False) == {
        "FileInput": {
            "queue_name": "FileInput",
            "count": 3,
            "exists": True,
        }
    }
    assert prod.graph().to_dict()["nodes"][0] == {
        "name": "FileInput",
        "class_name": "Demo.FileService",
        "kind": "component",
        "enabled": True,
        "category": "",
    }
    assert "queue=" not in str(prod.graph())


def test_production_queue_fetches_and_updates_runtime_metadata():
    director = MagicMock()
    director.export_production_queue_info.return_value = {
        "items": [{"item": "FileInput", "queue_name": "FileInput", "count": 2}]
    }
    prod = Production("Demo.Production", director=director)
    prod.service("FileInput", class_name="Demo.FileService")

    info = prod.queue()

    assert info == {"FileInput": {"queue_name": "FileInput", "count": 2}}
    assert prod.queue(refresh=False) == info
    assert prod.queue_info(refresh=False) == info
    assert "queue" not in prod.graph().to_dict()["nodes"][0]
    director.export_production_queue_info.assert_called_once_with("Demo.Production")


def test_production_from_dict_falls_back_to_host_setting_inference():
    exported = {
        "Demo.Production": {
            "Item": [
                {
                    "@Name": "FileInput",
                    "@ClassName": "Python.demo.FileService",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "Output",
                        "#text": "OrderOperation",
                    },
                },
                {
                    "@Name": "OrderOperation",
                    "@ClassName": "Python.demo.OrderOperation",
                },
            ]
        }
    }

    prod = Production.from_dict(
        exported,
        connections={"items": [{"item": "FileInput", "warnings": ["boom"]}]},
    )

    assert prod.resolve_target("FileInput.Output") == "OrderOperation"
    assert prod.graph().to_dict()["edges"][0]["inferred"] is True
    assert prod.graph().warnings == ("FileInput: boom",)

def test_production_from_dict_keeps_runtime_edge_without_matching_port():
    exported = {
        "Demo.Production": {
            "Item": [
                {"@Name": "Router", "@ClassName": "Demo.Router"},
                {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
            ]
        }
    }

    prod = Production.from_dict(
        exported,
        connections={"items": [{"item": "Router", "connections": ["OrderOperation"]}]},
    )

    graph = prod.graph()
    assert graph.to_dict()["edges"] == [
        {
            "source": "Router",
            "source_item": "Router",
            "source_port": "",
            "logical_name": "",
            "target": "OrderOperation",
            "runtime": True,
        }
    ]
    assert "(runtime) -> OrderOperation" in str(graph)


def test_production_from_iris_uses_export_and_runtime_connections():
    director = MagicMock()
    director.export_production.return_value = {
        "Demo.Production": {
            "Item": [
                {
                    "@Name": "FileInput",
                    "@ClassName": "Python.demo.FileService",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "Output",
                        "#text": "OrderOperation",
                    },
                },
                {
                    "@Name": "OrderOperation",
                    "@ClassName": "Python.demo.OrderOperation",
                },
            ]
        }
    }
    director.export_production_connections.return_value = {
        "items": [{"item": "FileInput", "connections": ["OrderOperation"]}]
    }

    prod = Production.from_iris("Demo.Production", director=director)

    director.export_production.assert_called_once_with("Demo.Production")
    director.export_production_connections.assert_called_once_with("Demo.Production")
    assert prod.item("FileInput").Output.resolve() == "OrderOperation"


def test_objectscript_component_uses_class_name_and_manual_port():
    prod = Production("Demo.Production")
    file = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
    output = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

    prod.connect(file.port("TargetConfigNames"), output)

    assert prod.to_dict()["Demo.Production"]["Item"][0]["@ClassName"] == (
        "EnsLib.File.PassthroughService"
    )
    assert prod.component_registrations() == ()
    assert prod.resolve_target("FileIn.TargetConfigNames") == "FileOut"


def test_component_crud_edits_python_graph_only():
    prod = Production("Demo.Production")
    file = prod.add_component("FileIn", class_name="EnsLib.File.PassthroughService")
    op = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")
    prod.connect(file.port("TargetConfigNames"), op)

    prod.update_component("FileIn", settings={"Limit": 10}, enabled=False)
    assert prod.item("FileIn").host_settings["Limit"] == 10
    assert prod.item("FileIn").enabled is False

    prod.disconnect("FileIn.TargetConfigNames")
    assert "TargetConfigNames" not in prod.item("FileIn").host_settings
    assert prod.graph().to_dict()["edges"] == []

    prod.connect(file.port("TargetConfigNames"), op)
    prod.delete_component("FileOut")

    assert prod.graph().to_dict()["edges"] == []
    with pytest.raises(ValueError, match="does not exist"):
        prod.item("FileOut")


def test_production_sync_registers_current_definition():
    prod = Production("Demo.Production")
    prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

    with patch.object(_Utils, "set_productions_settings") as mock_set:
        with patch("iop._local._LocalDirector.update_production") as mock_update:
            prod.sync(root_path="/tmp/iop")

    mock_set.assert_called_once_with([prod], "/tmp/iop")
    mock_update.assert_called_once()


def test_set_productions_settings_keeps_legacy_dicts_immutable(tmp_path):
    class TestComponent:
        pass

    production_list = [
        {
            "TestProduction": {
                "Item": [{"@Name": "TestItem", "@ClassName": TestComponent}]
            }
        }
    ]
    original = copy.deepcopy(production_list)

    with patch.object(_Utils, "register_component") as mock_register:
        with patch.object(_Utils, "register_production") as mock_prod:
            _Utils.set_productions_settings(production_list, str(tmp_path))

    assert production_list == original
    mock_register.assert_called_once()
    mock_prod.assert_called_once()


def test_set_productions_settings_supports_mixed_legacy_and_objects(tmp_path):
    legacy = {"Legacy.Production": {"Item": []}}
    prod = Production("Object.Production")
    prod.operation(OrderOperation)

    with patch.object(_Utils, "register_component") as mock_register:
        with patch.object(_Utils, "register_production") as mock_prod:
            _Utils.set_productions_settings([legacy, prod], str(tmp_path))

    mock_register.assert_called_once_with(
        OrderOperation.__module__,
        "OrderOperation",
        str(tmp_path),
        1,
        f"Python.{OrderOperation.__module__}.OrderOperation".replace("_", ""),
    )
    assert mock_prod.call_count == 2


def test_migration_plan_lists_production_objects_and_auto_components():
    prod = Production("Object.Production")
    prod.operation(OrderOperation)

    class Settings:
        CLASSES = {}
        PRODUCTIONS = [prod]

    plan = _Utils._build_migration_plan(Settings, ".")

    assert "Object.Production" in plan["productions"]
    assert (
        f"Python.{OrderOperation.__module__}.OrderOperation".replace("_", "")
        + f" -> {OrderOperation.__module__}.OrderOperation (component)"
        in plan["classes"]
    )


def test_business_host_request_helpers_resolve_port_targets():
    prod = Production("Demo.Production")
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    host = _BusinessHost()
    host.iris_handle = MagicMock()
    host.iris_handle.dispatchSendRequestSync.return_value = "ok"

    assert host.send_request_sync(file.Output, "") == "ok"
    host.iris_handle.dispatchSendRequestSync.assert_called_once_with(
        "OrderOperation", "", -1, None
    )


def test_business_host_request_helpers_reject_unresolved_ports_before_dispatch():
    prod = Production("Demo.Production")
    file = prod.service("FileInput", FileService)

    host = _BusinessHost()
    host.iris_handle = MagicMock()

    with pytest.raises(ValueError, match="not connected"):
        host.send_request_sync(file.Output, "")

    host.iris_handle.dispatchSendRequestSync.assert_not_called()


def test_business_process_send_request_async_resolves_port_targets():
    prod = Production("Demo.Production")
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    process = BusinessProcess()
    process.iris_handle = MagicMock()

    process.send_request_async(file.Output, "", response_required=False)

    process.iris_handle.dispatchSendRequestAsync.assert_called_once_with(
        "OrderOperation", "", 0, None, None
    )
