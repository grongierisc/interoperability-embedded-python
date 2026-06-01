import copy
import json
import os
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
            "origin": "authored",
            "interaction": "request",
        },
    )


def test_port_str_is_identity_not_runtime_resolution():
    prod = Production("Demo.Production")
    file = prod.service("FileInput", FileService)

    assert str(file.Output) == "FileInput.Output"
    with pytest.raises(ValueError, match="not connected"):
        file.Output.resolve()


def test_production_test_resolves_string_port_path_from_object_graph():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Test.Production",
        "Status": "running",
    }
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


def test_production_test_component_is_canonical_test_api():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Test.Production",
        "Status": "running",
    }
    director.test_component.return_value = "ok"
    prod = Production("Test.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    assert prod.test_component(orders, OrderRequest(order_id="123")) == "ok"

    director.test_component.assert_called_once()
    assert director.test_component.call_args.args[0] == "OrderOperation"


def test_production_test_resolves_only_from_object_graph():
    director = MagicMock()
    prod = Production("Demo.Production", director=director)

    with pytest.raises(ValueError, match="Production item does not exist: FileInput"):
        prod.test("FileInput.Output", OrderRequest(order_id="123"))

    director.export_production.assert_not_called()
    director.test_component.assert_not_called()


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


def test_production_test_fails_closed_when_status_cannot_be_checked():
    director = MagicMock()
    director.status_production.side_effect = RuntimeError("status unavailable")
    prod = Production("Demo.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    with pytest.raises(RuntimeError, match="could not verify production status"):
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


def test_production_lifecycle_methods_are_scoped_to_this_production():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Other.Production",
        "Status": "running",
    }
    prod = Production("Demo.Production", director=director)

    with pytest.raises(RuntimeError, match="Cannot stop production 'Demo.Production'"):
        prod.stop()
    with pytest.raises(
        RuntimeError,
        match="Cannot restart production 'Demo.Production'",
    ):
        prod.restart()
    with pytest.raises(
        RuntimeError,
        match="Cannot update production 'Demo.Production'",
    ):
        prod.update()
    with pytest.raises(RuntimeError, match="Cannot kill production 'Demo.Production'"):
        prod.kill()

    director.stop_production.assert_not_called()
    director.restart_production.assert_not_called()
    director.update_production.assert_not_called()
    director.shutdown_production.assert_not_called()


def test_production_lifecycle_methods_call_director_when_current_matches():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Demo.Production",
        "Status": "running",
    }
    prod = Production("Demo.Production", director=director)

    prod.stop()
    prod.restart()
    prod.update()
    prod.kill()

    director.stop_production.assert_called_once()
    director.restart_production.assert_called_once()
    director.update_production.assert_called_once()
    director.shutdown_production.assert_called_once()


def test_production_component_lifecycle_methods_are_scoped_to_this_production():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Other.Production",
        "Status": "running",
    }
    prod = Production("Demo.Production", director=director)
    orders = prod.operation(OrderOperation)

    with pytest.raises(
        RuntimeError,
        match="Cannot start component 'OrderOperation' in production 'Demo.Production'",
    ):
        prod.start_component(orders)
    with pytest.raises(
        RuntimeError,
        match="Cannot stop component 'OrderOperation' in production 'Demo.Production'",
    ):
        prod.stop_component(orders)
    with pytest.raises(
        RuntimeError,
        match="Cannot restart component 'OrderOperation' in production 'Demo.Production'",
    ):
        prod.restart_component(orders)

    director.start_component.assert_not_called()
    director.stop_component.assert_not_called()
    director.restart_component.assert_not_called()


def test_production_component_lifecycle_methods_call_director_when_current_matches():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Demo.Production",
        "Status": "running",
    }
    prod = Production("Demo.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    prod.start_component(orders)
    prod.stop_component("OrderOperation")
    prod.restart_component(file.Output)

    director.start_component.assert_called_once_with("OrderOperation")
    director.stop_component.assert_called_once_with("OrderOperation")
    director.restart_component.assert_called_once_with("OrderOperation")


def test_production_component_ref_retrieval_accepts_item_ref_and_port():
    prod = Production("Demo.Production")
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    assert prod.item("OrderOperation") is orders
    assert prod.component_ref("OrderOperation") is orders
    assert prod.component_ref(orders) is orders
    assert prod.component_ref(file.Output) is orders
    assert prod.component_ref("FileInput.Output") is orders
    assert prod.get_component("OrderOperation") is orders


def test_component_ref_runtime_methods_delegate_to_production():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Demo.Production",
        "Status": "running",
    }
    director.export_production_queue_info.return_value = {"items": []}
    director.test_component.return_value = "ok"
    prod = Production("Demo.Production", director=director)
    orders = prod.operation(OrderOperation)

    assert orders.inspect()["name"] == "OrderOperation"
    orders.start()
    orders.stop()
    orders.restart()
    assert orders.test(OrderRequest(order_id="123")) == "ok"

    director.start_component.assert_called_once_with("OrderOperation")
    director.stop_component.assert_called_once_with("OrderOperation")
    director.restart_component.assert_called_once_with("OrderOperation")
    director.test_component.assert_called_once()
    assert director.test_component.call_args.args[0] == "OrderOperation"


def test_production_inspect_component_includes_graph_and_runtime_info():
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Demo.Production",
        "Status": "running",
    }
    director.export_production_queue_info.return_value = {
        "items": [
            {
                "item": "OrderOperation",
                "queue_name": "OrderOperation",
                "count": 2,
            }
        ]
    }
    prod = Production("Demo.Production", director=director)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    info = prod.inspect_component("FileInput.Output")

    assert info["production"] == "Demo.Production"
    assert info["name"] == "OrderOperation"
    assert info["class_name"] == (
        f"Python.{OrderOperation.__module__}.OrderOperation".replace("_", "")
    )
    assert info["incoming"][0]["source"] == "FileInput.Output"
    assert info["outgoing"] == []
    assert info["runtime"]["is_running"] is True
    assert info["runtime"]["queue"]["count"] == 2
    director.export_production_queue_info.assert_called_once_with("Demo.Production")


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
            "origin": "runtime",
            "interaction": "request",
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


def test_production_diff_reports_no_changes_against_equivalent_definition():
    prod = Production("Demo.Production", testing_enabled=True)
    file = prod.service("FileInput", FileService, settings={"Limit": 10})
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    diff = prod.diff(Production.from_dict(prod.to_dict()))

    assert diff.has_changes is False
    assert diff.to_dict() == {
        "production": "Demo.Production",
        "has_changes": False,
        "changes": [],
    }
    assert "no changes" in str(diff)


def test_production_graph_diff_includes_edge_origin_metadata():
    prod = Production("Demo.Production", testing_enabled=True)
    file = prod.service("FileInput", FileService)
    orders = prod.operation(OrderOperation)
    prod.connect(file.Output, orders)

    imported = Production.from_dict(prod.to_dict())

    assert prod.diff(imported).has_changes is False
    graph_diff = prod.graph_diff(imported)

    assert graph_diff.has_changes is True
    assert {
        "action": "change",
        "kind": "connection",
        "path": "connections.FileInput.Output",
        "before": [
            {
                "target": "OrderOperation",
                "origin": "inferred",
                "interaction": "request",
                "logical_name": "",
                "metadata": {"source": "Host setting fallback"},
            }
        ],
        "after": [
            {
                "target": "OrderOperation",
                "origin": "authored",
                "interaction": "request",
                "logical_name": "orders",
            }
        ],
    } in graph_diff.to_dict()["changes"]


def test_production_diff_reports_items_settings_and_connections():
    current = Production("Demo.Production")
    current_file = current.service(
        "FileInput",
        class_name="Demo.OldFileService",
        settings={"Limit": 5},
    )
    old_orders = current.operation("OldOrderOperation", class_name="Demo.OldOrders")
    current.connect(current_file.port("Output"), old_orders)

    desired = Production("Demo.Production")
    desired_file = desired.service(
        "FileInput",
        FileService,
        settings={"Limit": 10},
    )
    orders = desired.operation(OrderOperation)
    desired.connect(desired_file.Output, orders)

    changes = desired.diff(current).to_dict()["changes"]

    assert {
        "action": "remove",
        "kind": "item",
        "path": "items.OldOrderOperation",
        "before": {
            "class_name": "Demo.OldOrders",
            "category": "",
            "pool_size": "1",
            "enabled": "true",
            "foreground": "false",
            "comment": "",
            "log_trace_events": "false",
            "schedule": "",
            "host_settings": {},
            "adapter_settings": {},
            "other_settings": [],
        },
    } in changes
    assert any(
        change["action"] == "add"
        and change["kind"] == "item"
        and change["path"] == "items.OrderOperation"
        for change in changes
    )
    assert {
        "action": "change",
        "kind": "item",
        "path": "items.FileInput.class_name",
        "before": "Demo.OldFileService",
        "after": f"Python.{FileService.__module__}.FileService".replace("_", ""),
    } in changes
    assert {
        "action": "change",
        "kind": "setting",
        "path": "items.FileInput.settings.Host.Limit",
        "before": "5",
        "after": "10",
    } in changes
    assert {
        "action": "change",
        "kind": "connection",
        "path": "connections.FileInput.Output",
        "before": ["OldOrderOperation"],
        "after": ["OrderOperation"],
    } in changes


def test_production_diff_without_argument_compares_with_iris_reconstruction():
    desired = Production("Demo.Production", director=MagicMock())
    file = desired.service("FileInput", FileService)
    orders = desired.operation(OrderOperation)
    desired.connect(file.Output, orders)
    desired._director.export_production.return_value = desired.to_dict()
    desired._director.export_production_connections.return_value = {
        "items": [{"item": "FileInput", "connections": ["OrderOperation"]}]
    }

    diff = desired.diff()

    assert diff.has_changes is False
    desired._director.export_production.assert_called_once_with("Demo.Production")
    desired._director.export_production_connections.assert_called_once_with(
        "Demo.Production"
    )


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
    assert prod.graph().to_dict()["edges"][0]["origin"] == "inferred"
    assert prod.graph().to_dict()["edges"][0]["metadata"] == {
        "source": "Host setting fallback"
    }
    assert prod.graph().warnings == ("FileInput: boom",)


def test_production_from_dict_does_not_infer_when_runtime_discovery_succeeds_empty():
    exported = {
        "Demo.Production": {
            "Item": [
                {
                    "@Name": "Router",
                    "@ClassName": "Demo.Router",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "TargetConfigNames",
                        "#text": "OrderOperation",
                    },
                },
                {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
            ]
        }
    }

    prod = Production.from_dict(
        exported,
        connections={"items": [{"item": "Router", "connections": []}]},
    )

    assert prod.graph().to_dict()["edges"] == []
    with pytest.raises(ValueError, match="not connected"):
        prod.resolve_target("Router.TargetConfigNames")


def test_production_graph_allows_multigraph_edges_but_port_resolution_is_strict():
    exported = {
        "Demo.Production": {
            "Item": [
                {
                    "@Name": "Router",
                    "@ClassName": "Demo.Router",
                    "Setting": {
                        "@Target": "Host",
                        "@Name": "TargetConfigNames",
                        "#text": "OrderA,OrderB",
                    },
                },
                {"@Name": "OrderA", "@ClassName": "Demo.OrderOperation"},
                {"@Name": "OrderB", "@ClassName": "Demo.OrderOperation"},
            ]
        }
    }

    prod = Production.from_dict(exported)
    edges = prod.graph().to_dict()["edges"]

    assert [edge["target"] for edge in edges] == ["OrderA", "OrderB"]
    assert all(edge["origin"] == "inferred" for edge in edges)
    with pytest.raises(ValueError, match="ambiguous"):
        prod.resolve_target("Router.TargetConfigNames")


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
            "origin": "runtime",
            "interaction": "request",
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


def test_production_sync_restores_namespace_env(monkeypatch):
    seen = []
    monkeypatch.setenv("IRISNAMESPACE", "ORIGINAL")
    prod = Production("Demo.Production", namespace="TARGET")
    prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

    def capture_namespace(*args, **kwargs):
        seen.append(os.environ.get("IRISNAMESPACE"))

    with patch.object(
        _Utils,
        "set_productions_settings",
        side_effect=capture_namespace,
    ):
        with patch("iop._local._LocalDirector.update_production"):
            prod.sync(root_path="/tmp/iop")

    assert seen == ["TARGET"]
    assert os.environ["IRISNAMESPACE"] == "ORIGINAL"


def test_production_runtime_director_restores_namespace_env(monkeypatch):
    seen = []
    monkeypatch.setenv("IRISNAMESPACE", "ORIGINAL")
    prod = Production("Demo.Production", namespace="TARGET")

    def capture_status():
        seen.append(os.environ.get("IRISNAMESPACE"))
        return {"Production": "Demo.Production", "Status": "running"}

    with patch("iop._remote.get_remote_settings", return_value=None):
        with patch(
            "iop._local._LocalDirector.status_production",
            side_effect=capture_status,
        ):
            assert prod.status() == {
                "Production": "Demo.Production",
                "Status": "running",
            }

    assert seen == ["TARGET"]
    assert os.environ["IRISNAMESPACE"] == "ORIGINAL"


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
