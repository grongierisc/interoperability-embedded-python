import ast
import copy
import inspect
import json
import os
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from iop import (
    BusinessOperation,
    BusinessProcess,
    BusinessService,
    ComponentItem,
    Field,
    InboundAdapter,
    Message,
    OperationItem,
    PersistentMessage,
    PollingBusinessService,
    ProcessItem,
    Production,
    ProductionValidationError,
    ProductionValidationWarning,
    Route,
    ServiceItem,
    controls,
    target,
)
from iop.components.business_host import _BusinessHost
from iop.migration import utils as migration_utils


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class NativeOrderMessage(PersistentMessage):
    OrderId: str = Field(required=True)


class FileService(PollingBusinessService):
    Output = target()


class OrderProcess(BusinessProcess):
    Output = target()


class OrderOperation(BusinessOperation):
    pass


class PythonInboundAdapter(InboundAdapter):
    pass


class AdapterService(BusinessService):
    @staticmethod
    def get_adapter_type():
        return f"Python.{PythonInboundAdapter.__module__}.PythonInboundAdapter".replace(
            "_",
            "",
        )


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

    assert prod.graph().to_dict()["edges"] == [
        {
            "source": "FileInput.Output",
            "source_item": "FileInput",
            "source_target_setting": "Output",
            "target": "OrderOperation",
            "origin": "authored",
            "interaction": "request",
        },
    ]


def test_production_level_settings_round_trip_and_render_to_python():
    prod = Production(
        "Demo.Production",
        shutdown_timeout=30,
        update_timeout=7,
        alert_notification_manager="Alerts.Manager",
        alert_notification_operation="Alerts.Operation",
        alert_notification_recipients="ops@example.com",
        alert_action_window=15,
    )

    data = prod.to_dict()["Demo.Production"]
    settings = {setting["@Name"]: setting["#text"] for setting in data["Setting"]}

    assert settings == {
        "ShutdownTimeout": "30",
        "UpdateTimeout": "7",
        "AlertNotificationManager": "Alerts.Manager",
        "AlertNotificationOperation": "Alerts.Operation",
        "AlertNotificationRecipients": "ops@example.com",
        "AlertActionWindow": "15",
    }
    assert "Setting" not in Production("Default.Production").to_dict()[
        "Default.Production"
    ]

    imported = Production.from_dict(prod.to_dict())
    assert imported.shutdown_timeout == "30"
    assert imported.update_timeout == "7"
    assert imported.alert_notification_manager == "Alerts.Manager"
    assert prod.diff(imported).has_changes is False

    text = prod.to_python()
    assert "shutdown_timeout=30" in text
    assert "update_timeout=7" in text
    assert "alert_notification_manager='Alerts.Manager'" in text


def test_production_message_registration_api_deduplicates_identical_entries():
    prod = Production("Demo.Production")

    result = prod.message("Demo.Msg.NativeOrderMessage", NativeOrderMessage)
    prod.message("Demo.Msg.NativeOrderMessage", NativeOrderMessage)

    assert result is prod
    registrations = prod.message_registrations()
    assert len(registrations) == 1
    assert registrations[0].iris_classname == "Demo.Msg.NativeOrderMessage"
    assert registrations[0].message_class is NativeOrderMessage
    assert registrations[0].sync_schema is True


def test_production_message_registration_validates_inputs():
    class OtherNativeMessage(PersistentMessage):
        Value: str = Field(required=True)

    prod = Production("Demo.Production")
    prod.message("Demo.Msg.NativeOrderMessage", NativeOrderMessage)

    with pytest.raises(ValueError, match="IRIS classname"):
        prod.message("", NativeOrderMessage)
    with pytest.raises(TypeError, match="PersistentMessage"):
        prod.message("Demo.Msg.OrderRequest", OrderRequest)
    with pytest.raises(ValueError, match="already registered"):
        prod.message("Demo.Msg.NativeOrderMessage", OtherNativeMessage)
    with pytest.raises(ValueError, match="already registered"):
        prod.message("Demo.Msg.OtherNativeOrderMessage", NativeOrderMessage)
    with pytest.raises(ValueError, match="sync_schema"):
        prod.message(
            "Demo.Msg.NativeOrderMessage",
            NativeOrderMessage,
            sync_schema=False,
        )


def test_production_to_python_renders_brownfield_draft():
    prod = Production("Demo.Production", testing_enabled=True, actor_pool_size=3)
    file_input = prod.component(
        "File Input",
        class_name="EnsLib.File.PassthroughService",
        settings={
            "Limit": "10",
            "TargetConfigNames": "Order Operation",
        },
        adapter_settings={"FilePath": "/data/in"},
    )
    order_operation = prod.component(
        "Order Operation",
        class_name="Demo.OrderOperation",
    )
    prod.connect(file_input.target_setting("TargetConfigNames"), order_operation)

    text = prod.to_python()

    ast.parse(text)
    assert "from iop import Production" in text
    assert "prod = Production('Demo.Production'," in text
    assert "testing_enabled=True" in text
    assert "actor_pool_size=3" in text
    assert "file_input = prod.component(" in text
    assert "order_operation = prod.component(" in text
    assert "class_name='EnsLib.File.PassthroughService'" in text
    assert "'Limit': '10'" in text
    assert "'TargetConfigNames':" not in text
    assert "adapter_settings={" in text
    assert (
        "prod.connect(file_input.target_setting('TargetConfigNames'), order_operation)"
        in text
    )
    assert text.endswith("PRODUCTIONS = [prod]\n")


def test_production_to_mermaid_renders_draft_graph():
    prod = Production("Demo.Production")
    file_input = prod.component(
        "File Input",
        class_name="EnsLib.File.PassthroughService",
    )
    order_operation = prod.component(
        "Order & Operation",
        class_name='Demo.Order"Operation"',
    )
    prod.connect(file_input.target_setting("TargetConfigNames"), order_operation)

    text = prod.to_mermaid()

    assert text == prod.graph().to_mermaid()
    assert text.startswith("flowchart LR\n")
    assert "%% Production: Demo.Production" in text
    assert (
        'node_File_Input["File Input<br/>EnsLib.File.PassthroughService"]'
        in text
    )
    assert (
        'node_Order_Operation["Order &amp; Operation<br/>'
        "Demo.Order&quot;Operation&quot;\"]"
        in text
    )
    assert (
        'node_File_Input -- "TargetConfigNames" --> node_Order_Operation'
        in text
    )


def test_production_connect_rejects_message_metadata():
    prod = Production("Demo.Production")
    file_input = prod.service("FileInput", FileService)
    order_operation = prod.operation("OrderOperation", OrderOperation)

    with pytest.raises(TypeError, match="message"):
        prod.connect(file_input.Output, order_operation, message=OrderRequest)


def test_production_to_mermaid_can_group_by_production_role():
    prod = Production("Demo.Production")
    file_input = prod.service("FileInput", FileService)
    order_process = prod.process("OrderProcess", OrderProcess)
    order_operation = prod.operation("OrderOperation", OrderOperation)
    prod.connect(file_input.Output, order_process)
    prod.connect(order_process.Output, order_operation)

    text = prod.to_mermaid()

    assert 'subgraph group_service["Services"]' in text
    assert 'subgraph group_process["Processes"]' in text
    assert 'subgraph group_operation["Operations"]' in text
    assert "    direction TB" in text
    assert "  node_FileInput ~~~ node_OrderProcess" in text
    assert "  node_OrderProcess ~~~ node_OrderOperation" in text
    assert 'node_FileInput -- "Output" --> node_OrderProcess' in text


def test_production_to_mermaid_groups_imported_python_proxy_roles():
    prod = Production.from_dict(
        {
            "Demo.MermaidShowcaseProduction": {
                "Item": [
                    {
                        "@Name": "Claim API",
                        "@ClassName": "Python.main.ClaimApiService",
                    },
                    {
                        "@Name": "Validate Claim",
                        "@ClassName": "Python.main.ClaimValidationProcess",
                    },
                    {
                        "@Name": "Fraud Score",
                        "@ClassName": "Python.main.FraudScoreOperation",
                    },
                ]
            }
        }
    )

    text = prod.to_mermaid()

    assert 'subgraph group_service["Services"]' in text
    assert 'node_Claim_API["Claim API<br/>Python.main.ClaimApiService"]' in text
    assert 'subgraph group_process["Processes"]' in text
    assert (
        'node_Validate_Claim["Validate Claim<br/>'
        'Python.main.ClaimValidationProcess"]' in text
    )
    assert 'subgraph group_operation["Operations"]' in text
    assert (
        'node_Fraud_Score["Fraud Score<br/>Python.main.FraudScoreOperation"]'
        in text
    )


def test_production_from_dict_uses_runtime_kind_metadata():
    prod = Production.from_dict(
        {
            "Demo.Production": {
                "Item": [
                    {"@Name": "CustomInput", "@ClassName": "Demo.CustomInput"},
                    {"@Name": "CustomWorker", "@ClassName": "Demo.CustomWorker"},
                ]
            }
        },
        connections={
            "items": [
                {
                    "item": "CustomInput",
                    "kind": "service",
                    "connections": ["CustomWorker"],
                },
                {
                    "item": "CustomWorker",
                    "kind": "operation",
                    "connections": [],
                },
            ]
        },
    )

    nodes = {node["name"]: node for node in prod.graph().to_dict()["nodes"]}
    assert nodes["CustomInput"]["kind"] == "service"
    assert nodes["CustomWorker"]["kind"] == "operation"


def test_production_from_dict_infers_python_send_request_targets_from_source(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "reddit.py").write_text(
        """
class RedditService:
    def on_init(self):
        if not hasattr(self, "target"):
            self.target = "Python.FilterPostRoutingRule"

    def on_poll(self):
        self.send_request_sync(self.target, object())


class FilterPostRoutingRule:
    def on_init(self):
        if not hasattr(self, "target"):
            self.target = "Python.FileOperation"

    def on_message(self, request):
        return self.send_request_sync(target=self.target, request=request)
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    prod = Production.from_dict(
        {
            "PEX.Production": {
                "Item": [
                    {
                        "@Name": "RedditService",
                        "@ClassName": "Demo.RedditServiceProxy",
                        "Setting": [
                            {
                                "@Target": "Host",
                                "@Name": "%module",
                                "#text": "reddit",
                            },
                            {
                                "@Target": "Host",
                                "@Name": "%classname",
                                "#text": "RedditService",
                            },
                        ],
                    },
                    {
                        "@Name": "Python.FilterPostRoutingRule",
                        "@ClassName": "Demo.FilterPostRoutingRuleProxy",
                        "Setting": [
                            {
                                "@Target": "Host",
                                "@Name": "%module",
                                "#text": "reddit",
                            },
                            {
                                "@Target": "Host",
                                "@Name": "%classname",
                                "#text": "FilterPostRoutingRule",
                            },
                        ],
                    },
                    {
                        "@Name": "Python.FileOperation",
                        "@ClassName": "Demo.FileOperationProxy",
                    },
                ]
            }
        },
        connections={
            "items": [
                {"item": "RedditService", "connections": []},
                {"item": "Python.FilterPostRoutingRule", "connections": []},
                {"item": "Python.FileOperation", "connections": []},
            ]
        },
    )

    edges = {
        (edge["source_item"], edge["target"]): edge
        for edge in prod.graph().to_dict()["edges"]
    }

    assert edges[
        ("RedditService", "Python.FilterPostRoutingRule")
    ]["origin"] == "inferred"
    assert edges[
        ("Python.FilterPostRoutingRule", "Python.FileOperation")
    ]["metadata"] == {
        "source": "Python source",
        "detail": "send_request_sync self.target",
    }
    assert edges[
        ("Python.FilterPostRoutingRule", "Python.FileOperation")
    ]["interaction"] == "sync"


def test_production_from_dict_prefers_python_host_setting_over_source_default(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "bench_bp.py").write_text(
        """
class BenchIoPProcess:
    target = target()

    def on_init(self):
        if not hasattr(self, "target"):
            self.target = "Python.BenchIoPOperation"

    def on_message(self, request):
        self.send_request_sync(self.target, request)
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    classpaths = str(tmp_path)

    prod = Production.from_dict(
        {
            "Bench.Production": {
                "Item": [
                    {
                        "@Name": "Python.BenchIoPProcess",
                        "@ClassName": "Python.BenchIoPProcess",
                        "Setting": [
                            {
                                "@Target": "Host",
                                "@Name": "%classpaths",
                                "#text": classpaths,
                            },
                            {
                                "@Target": "Host",
                                "@Name": "target",
                                "#text": "Python.BenchIoPOperation",
                            },
                        ],
                    },
                    {
                        "@Name": "Python.BenchIoPProcess.To.Cls",
                        "@ClassName": "Python.BenchIoPProcess",
                        "Setting": [
                            {
                                "@Target": "Host",
                                "@Name": "%classpaths",
                                "#text": classpaths,
                            },
                            {
                                "@Target": "Host",
                                "@Name": "target",
                                "#text": "Bench.Operation",
                            },
                        ],
                    },
                    {
                        "@Name": "Python.BenchIoPOperation",
                        "@ClassName": "Python.BenchIoPOperation",
                    },
                    {"@Name": "Bench.Operation", "@ClassName": "Bench.Operation"},
                ]
            }
        },
        connections={
            "items": [
                {
                    "item": "Python.BenchIoPProcess",
                    "iop": True,
                    "module": "bench_bp",
                    "classname": "BenchIoPProcess",
                    "classpaths": classpaths,
                    "connections": [],
                },
                {
                    "item": "Python.BenchIoPProcess.To.Cls",
                    "iop": True,
                    "module": "bench_bp",
                    "classname": "BenchIoPProcess",
                    "classpaths": classpaths,
                    "connections": [],
                },
            ]
        },
    )

    edges = {
        (edge["source_item"], edge["target"]): edge
        for edge in prod.graph().to_dict()["edges"]
    }

    assert (
        "Python.BenchIoPProcess.To.Cls",
        "Python.BenchIoPOperation",
    ) not in edges
    assert edges[
        ("Python.BenchIoPProcess", "Python.BenchIoPOperation")
    ]["interaction"] == "sync"
    assert edges[
        ("Python.BenchIoPProcess.To.Cls", "Bench.Operation")
    ]["interaction"] == "sync"


def test_production_from_dict_does_not_treat_python_prefix_as_python_source(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "source.py").write_text(
        """
class PretendSource:
    def on_message(self, request):
        return self.send_request_sync("PythonTarget", request)
""",
        encoding="utf-8",
    )
    (tmp_path / "PretendSource.cls").write_text(
        """
Class Python.PretendSource Extends Ens.BusinessProcess
{

Method OnRequest(request As Ens.Request) As %Status
{
    Do ..SendRequestSync("ObjectScriptTarget", request)
    Quit $$$OK
}

}
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    prod = Production.from_dict(
        {
            "Demo.Production": {
                "Item": [
                    {"@Name": "Source", "@ClassName": "Python.PretendSource"},
                    {"@Name": "PythonTarget", "@ClassName": "Demo.PythonTarget"},
                    {
                        "@Name": "ObjectScriptTarget",
                        "@ClassName": "Demo.ObjectScriptTarget",
                    },
                ]
            }
        }
    )

    edges = {
        (edge["source_item"], edge["target"]): edge
        for edge in prod.graph().to_dict()["edges"]
    }

    assert ("Source", "PythonTarget") not in edges
    assert edges[("Source", "ObjectScriptTarget")]["metadata"] == {
        "source": "ObjectScript source",
        "detail": "SendRequestSync literal",
    }
    assert edges[("Source", "ObjectScriptTarget")]["interaction"] == "sync"


def test_production_from_dict_uses_runtime_iop_metadata_for_python_source(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "worker.py").write_text(
        """
class SourceProcess:
    def on_message(self, request):
        return self.send_request_sync("TargetOperation", request)
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    prod = Production.from_dict(
        {
            "Demo.Production": {
                "Item": [
                    {"@Name": "SourceProcess", "@ClassName": "Demo.SourceProxy"},
                    {"@Name": "TargetOperation", "@ClassName": "Demo.TargetProxy"},
                ]
            }
        },
        connections={
            "items": [
                {
                    "item": "SourceProcess",
                    "iop": True,
                    "module": "worker",
                    "classname": "SourceProcess",
                    "connections": [],
                },
                {"item": "TargetOperation", "connections": []},
            ]
        },
    )

    edges = prod.graph().to_dict()["edges"]

    assert edges == [
        {
            "source": "SourceProcess",
            "source_item": "SourceProcess",
            "source_target_setting": "",
            "target": "TargetOperation",
            "origin": "inferred",
            "interaction": "sync",
            "metadata": {
                "source": "Python source",
                "detail": "send_request_sync literal",
            },
            "inferred": True,
        }
    ]


def test_production_from_dict_uses_iop_flag_for_python_class_name_fallback(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "bs.py").write_text(
        """
class RedditService:
    def on_poll(self):
        self.send_request_sync("Python.FilterPostRoutingRule", object())
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    prod = Production.from_dict(
        {
            "PEX.Production": {
                "Item": [
                    {
                        "@Name": "Python.RedditService",
                        "@ClassName": "Python.RedditService",
                    },
                    {
                        "@Name": "Python.FilterPostRoutingRule",
                        "@ClassName": "Python.FilterPostRoutingRule",
                    },
                ]
            }
        },
        connections={
            "items": [
                {"item": "Python.RedditService", "iop": True, "connections": []},
                {"item": "Python.FilterPostRoutingRule", "connections": []},
            ]
        },
    )

    edges = prod.graph().to_dict()["edges"]

    assert edges == [
        {
            "source": "Python.RedditService",
            "source_item": "Python.RedditService",
            "source_target_setting": "",
            "target": "Python.FilterPostRoutingRule",
            "origin": "inferred",
            "interaction": "sync",
            "metadata": {
                "source": "Python source",
                "detail": "send_request_sync literal",
            },
            "inferred": True,
        }
    ]


def test_production_from_dict_uses_runtime_classpaths_for_python_source(
    tmp_path,
    monkeypatch,
):
    source_dir = tmp_path / "python"
    source_dir.mkdir()
    (source_dir / "bs.py").write_text(
        """
class RedditService:
    def on_poll(self):
        self.send_request_sync("Python.FilterPostRoutingRule", object())
""",
        encoding="utf-8",
    )
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    monkeypatch.chdir(cwd)

    prod = Production.from_dict(
        {
            "PEX.Production": {
                "Item": [
                    {
                        "@Name": "Python.RedditService",
                        "@ClassName": "Python.RedditService",
                    },
                    {
                        "@Name": "Python.FilterPostRoutingRule",
                        "@ClassName": "Python.FilterPostRoutingRule",
                    },
                ]
            }
        },
        connections={
            "items": [
                {
                    "item": "Python.RedditService",
                    "iop": True,
                    "module": "bs",
                    "classname": "RedditService",
                    "classpaths": str(source_dir),
                    "connections": [],
                },
                {"item": "Python.FilterPostRoutingRule", "connections": []},
            ]
        },
    )

    edges = prod.graph().to_dict()["edges"]

    assert edges[0]["source_item"] == "Python.RedditService"
    assert edges[0]["target"] == "Python.FilterPostRoutingRule"
    assert edges[0]["interaction"] == "sync"


def test_production_from_dict_infers_objectscript_send_request_targets_from_source(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "Router.cls").write_text(
        """
Class Demo.Router Extends Ens.BusinessProcess
{

Property TargetConfigName As %String [ InitialExpression = "ArchiveOperation" ];

Method OnRequest(request As Ens.Request) As %Status
{
    Do ..SendRequestSync("OrderOperation", request)
    Do ..SendRequestAsync(..TargetConfigName, request)
    Quit $$$OK
}

}
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    prod = Production.from_dict(
        {
            "Demo.Production": {
                "Item": [
                    {"@Name": "Router", "@ClassName": "Demo.Router"},
                    {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
                    {
                        "@Name": "ArchiveOperation",
                        "@ClassName": "Demo.ArchiveOperation",
                    },
                ]
            }
        }
    )

    edges = {
        (edge["source_item"], edge["target"]): edge
        for edge in prod.graph().to_dict()["edges"]
    }

    assert edges[("Router", "OrderOperation")]["metadata"] == {
        "source": "ObjectScript source",
        "detail": "SendRequestSync literal",
    }
    assert edges[("Router", "OrderOperation")]["interaction"] == "sync"
    assert edges[("Router", "ArchiveOperation")]["metadata"] == {
        "source": "ObjectScript source",
        "detail": "SendRequestAsync ..TargetConfigName",
    }
    assert edges[("Router", "ArchiveOperation")]["interaction"] == "async"

    text = prod.to_mermaid()
    assert 'node_Router <-- "(runtime) | inferred | sync" --> node_OrderOperation' in text
    assert (
        'node_Router -- "(runtime) | inferred | async" --> node_ArchiveOperation'
        in text
    )


def test_production_from_dict_enriches_runtime_edges_with_source_interaction(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "Router.cls").write_text(
        """
Class Demo.Router Extends Ens.BusinessProcess
{

Method OnRequest(request As Ens.Request) As %Status
{
    Do ..SendRequestSync("OrderOperation", request)
    Quit $$$OK
}

}
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    prod = Production.from_dict(
        {
            "Demo.Production": {
                "Item": [
                    {"@Name": "Router", "@ClassName": "Demo.Router"},
                    {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
                ]
            }
        },
        connections={
            "items": [
                {"item": "Router", "connections": ["OrderOperation"]},
                {"item": "OrderOperation", "connections": []},
            ]
        },
    )

    edges = prod.graph().to_dict()["edges"]

    assert len(edges) == 1
    assert edges[0]["origin"] == "runtime"
    assert edges[0]["interaction"] == "sync"
    assert edges[0]["metadata"] == {
        "source": "ObjectScript source",
        "detail": "SendRequestSync literal",
    }


def test_production_to_class_renders_declarative_draft():
    prod = Production("Demo.DeclarativeProduction", testing_enabled=True)
    file_input = prod.service(
        "FileInput",
        class_name="EnsLib.File.PassthroughService",
        settings={"Limit": "10"},
        adapter_settings={"FilePath": "/data/in"},
    )
    order_operation = prod.operation(
        "OrderOperation",
        class_name="EnsLib.File.PassthroughOperation",
    )
    prod.connect(file_input.target_setting("TargetConfigNames"), order_operation)

    text = prod.to_class()

    ast.parse(text)
    assert "from iop import Production, OperationItem, ServiceItem, Route" in text
    assert "class DeclarativeProduction(Production):" in text
    assert "name = 'Demo.DeclarativeProduction'" in text
    assert "testing_enabled = True" in text
    assert "services = (" in text
    assert "ServiceItem(" in text
    assert "'EnsLib.File.PassthroughService'" in text
    assert "settings={" in text
    assert "adapter_settings={" in text
    assert "routes=(Route('TargetConfigNames', 'OrderOperation'),)" in text
    assert "operations = (" in text
    assert "OperationItem(" in text
    assert text.endswith("PRODUCTIONS = [DeclarativeProduction()]\n")


def test_production_to_class_uses_component_item_for_unknown_roles():
    prod = Production("Demo.GenericProduction")
    prod.component("CustomHost", class_name="Demo.CustomService")

    text = prod.to_class()

    ast.parse(text)
    assert "ComponentItem" in text
    assert "components = (" in text
    assert "ComponentItem(" in text
    assert "ServiceItem(" not in text
    assert "PRODUCTIONS = [GenericProduction()]" in text


def test_production_to_class_warns_for_string_python_proxies():
    prod = Production.from_dict(
        {
            "Demo.ImportedProduction": {
                "Item": [
                    {
                        "@Name": "FileInput",
                        "@ClassName": "Python.demo.FileService",
                    }
                ]
            }
        }
    )

    text = prod.to_class()

    ast.parse(text)
    assert "replace Python.* string class names" in text
    assert "replace this proxy class name with the Python" in text
    assert "ServiceItem(" in text


def test_declarative_production_string_class_names_match_instance_shape():
    class MyProduction(Production):
        name = "HelloWorld.Production"
        testing_enabled = True
        services = [
            ServiceItem(
                "MyServiceName",
                "HelloWorld.MyService",
                settings={"Limit": 10},
                routes=[Route("TargetConfigNames", "MyProcessName")],
            )
        ]
        processes = [
            ProcessItem(
                "MyProcessName",
                "HelloWorld.MyProcess",
                routes=[Route("TargetConfigNames", "MyOperationName")],
            )
        ]
        operations = [
            OperationItem("MyOperationName", "HelloWorld.MyOperation"),
        ]

    prod = MyProduction()

    assert isinstance(prod, Production)
    data = prod.to_dict()["HelloWorld.Production"]
    assert data["@TestingEnabled"] == "true"
    assert [item["@Name"] for item in data["Item"]] == [
        "MyServiceName",
        "MyProcessName",
        "MyOperationName",
    ]
    assert [item["@ClassName"] for item in data["Item"]] == [
        "HelloWorld.MyService",
        "HelloWorld.MyProcess",
        "HelloWorld.MyOperation",
    ]

    service_settings = {
        (setting["@Target"], setting["@Name"]): setting["#text"]
        for setting in data["Item"][0]["Setting"]
    }
    assert service_settings[("Host", "Limit")] == "10"
    assert service_settings[("Host", "TargetConfigNames")] == "MyProcessName"

    assert prod.graph().to_dict()["edges"] == [
        {
            "source": "MyServiceName.TargetConfigNames",
            "source_item": "MyServiceName",
            "source_target_setting": "TargetConfigNames",
            "target": "MyProcessName",
            "origin": "authored",
            "interaction": "request",
        },
        {
            "source": "MyProcessName.TargetConfigNames",
            "source_item": "MyProcessName",
            "source_target_setting": "TargetConfigNames",
            "target": "MyOperationName",
            "origin": "authored",
            "interaction": "request",
        },
    ]


def test_declarative_production_supports_generic_component_items():
    class GenericProduction(Production):
        name = "Demo.GenericProduction"
        components = [
            ComponentItem(
                "CustomHost",
                "Demo.CustomHost",
                other_settings=[
                    {"@Target": "Custom", "@Name": "Preserved", "#text": "yes"}
                ],
            )
        ]

    prod = GenericProduction()

    assert prod.to_dict()["Demo.GenericProduction"]["Item"][0]["@ClassName"] == (
        "Demo.CustomHost"
    )
    assert prod.item("CustomHost").other_settings == [
        {"@Target": "Custom", "@Name": "Preserved", "#text": "yes"}
    ]


def test_declarative_production_python_classes_keep_target_routes():
    class DeclarativeProduction(Production):
        name = "Demo.DeclarativeProduction"
        services = [
            ServiceItem(
                "FileInput",
                FileService,
                routes=[Route(FileService.Output, "OrderOperation")],
            )
        ]
        operations = [OperationItem("OrderOperation", OrderOperation)]

    prod = DeclarativeProduction()
    data = prod.to_dict()["Demo.DeclarativeProduction"]

    assert data["Item"][0]["@ClassName"] == (
        f"Python.{FileService.__module__}.{FileService.__name__}".replace("_", "")
    )
    assert data["Item"][1]["@ClassName"] == (
        f"Python.{OrderOperation.__module__}.{OrderOperation.__name__}".replace(
            "_", ""
        )
    )
    assert prod.item("FileInput").Output.resolve() == "OrderOperation"
    assert prod.graph().to_dict()["edges"][0]["source_target_setting"] == "Output"


def test_declarative_route_rejects_descriptor_from_another_component():
    class AlternateService(PollingBusinessService):
        OtherOutput = target()

    class InvalidProduction(Production):
        services = [
            ServiceItem(
                "FileInput",
                FileService,
                routes=[Route(AlternateService.OtherOutput, "OrderOperation")],
            )
        ]
        operations = [OperationItem("OrderOperation", OrderOperation)]

    with pytest.raises(ValueError, match="belongs to"):
        InvalidProduction()


def test_declarative_production_name_defaults_and_constructor_overrides():
    class DefaultNameProduction(Production):
        operations = [OperationItem("OrderOperation", "Demo.OrderOperation")]

    class NamedProduction(Production):
        name = "Demo.NamedProduction"
        testing_enabled = True
        actor_pool_size = 4
        shutdown_timeout = 30
        operations = [OperationItem("OrderOperation", "Demo.OrderOperation")]

    assert DefaultNameProduction().name == (
        f"{DefaultNameProduction.__module__}.DefaultNameProduction"
    )

    prod = NamedProduction()
    assert prod.name == "Demo.NamedProduction"
    assert prod.testing_enabled is True
    assert prod.actor_pool_size == 4
    assert prod.shutdown_timeout == 30

    override = NamedProduction("Demo.OverrideProduction", testing_enabled=False)
    assert override.name == "Demo.OverrideProduction"
    assert override.testing_enabled is False
    assert override.actor_pool_size == 4


def test_production_constructor_does_not_expose_hydration_flag():
    assert "_hydrate_declarations" not in inspect.signature(Production).parameters


def test_declarative_production_routes_support_fanout_and_port_aliases():
    class FanoutProduction(Production):
        name = "Demo.FanoutProduction"
        services = [
            ServiceItem(
                "Router",
                "Demo.Router",
                routes=[Route("target_config_names", ["First", "Second"])],
            )
        ]
        operations = [
            OperationItem("First", "Demo.First"),
            OperationItem("Second", "Demo.Second"),
        ]

    prod = FanoutProduction()

    assert prod.item("Router").host_settings["TargetConfigNames"] == "First,Second"
    assert [
        (edge.source_target_setting, edge.target)
        for edge in prod.graph().edges
    ] == [
        ("TargetConfigNames", "First"),
        ("TargetConfigNames", "Second"),
    ]


def test_declarative_routes_accept_item_declarations_as_targets():
    first = OperationItem("First", "Demo.First")
    second = OperationItem("Second", "Demo.Second")

    class ItemReferenceProduction(Production):
        name = "Demo.ItemReferenceProduction"
        services = (
            ServiceItem(
                "Router",
                "Demo.Router",
                routes=(Route("target_config_names", (first, second)),),
            ),
        )
        operations = (first, second)

    prod = ItemReferenceProduction()

    assert prod.item("Router").host_settings["TargetConfigNames"] == "First,Second"
    assert [(edge.source_target_setting, edge.target) for edge in prod.graph().edges] == [
        ("TargetConfigNames", "First"),
        ("TargetConfigNames", "Second"),
    ]


def test_declarative_production_migration_plan_registers_python_classes():
    class ObjectProduction(Production):
        name = "Object.Production"
        operations = [OperationItem("OrderOperation", OrderOperation)]

    class Settings:
        CLASSES = {}
        PRODUCTIONS = [ObjectProduction()]

    plan = migration_utils._build_migration_plan(Settings, ".")

    assert "Object.Production" in plan["productions"]
    assert (
        f"Python.{OrderOperation.__module__}.OrderOperation".replace("_", "")
        + f" -> {OrderOperation.__module__}.OrderOperation (component)"
        in plan["classes"]
    )


def test_declarative_production_from_dict_does_not_hydrate_class_items():
    class DeclarativeProduction(Production):
        name = "Demo.DeclarativeProduction"
        operations = [OperationItem("DeclaredOperation", "Demo.DeclaredOperation")]

    imported = DeclarativeProduction.from_dict(
        {
            "Imported.Production": {
                "Item": [
                    {
                        "@Name": "ImportedOperation",
                        "@ClassName": "Demo.ImportedOperation",
                    }
                ]
            }
        }
    )

    assert imported.name == "Imported.Production"
    assert [item.name for item in imported.items] == ["ImportedOperation"]


def test_declarative_production_rejects_invalid_declarations():
    class DuplicateItemProduction(Production):
        services = [ServiceItem("Duplicate", "Demo.Service")]
        operations = [OperationItem("Duplicate", "Demo.Operation")]

    with pytest.raises(ValueError, match="already exists"):
        DuplicateItemProduction()

    class MissingTargetProduction(Production):
        services = [
            ServiceItem(
                "Router",
                "Demo.Router",
                routes=[Route("TargetConfigNames", "Missing")],
            )
        ]

    with pytest.raises(ValueError, match="Production item does not exist: Missing"):
        MissingTargetProduction()

    class DuplicateSettingsProduction(Production):
        operations = [
            OperationItem(
                "Operation",
                "Demo.Operation",
                settings={"Limit": 1},
                host_settings={"Limit": 2},
            )
        ]

    with pytest.raises(ValueError, match="duplicate Host setting keys"):
        DuplicateSettingsProduction()

    class RouteSettingConflictProduction(Production):
        services = [
            ServiceItem(
                "Router",
                "Demo.Router",
                settings={"TargetConfigNames": "Operation"},
                routes=[Route("target_config_names", "Operation")],
            )
        ]
        operations = [OperationItem("Operation", "Demo.Operation")]

    with pytest.raises(ValueError, match="Route only"):
        RouteSettingConflictProduction()


def test_declarative_production_to_python_keeps_existing_instance_style():
    class DeclarativeProduction(Production):
        name = "Demo.DeclarativeProduction"
        services = [
            ServiceItem(
                "FileInput",
                "EnsLib.File.PassthroughService",
                routes=[Route("TargetConfigNames", "FileOut")],
            )
        ]
        operations = [
            OperationItem("FileOut", "EnsLib.File.PassthroughOperation"),
        ]

    text = DeclarativeProduction().to_python()

    ast.parse(text)
    assert "ServiceItem" not in text
    assert "class DeclarativeProduction" not in text
    assert "prod = Production('Demo.DeclarativeProduction')" in text
    assert "prod.connect(fileinput.target_setting('TargetConfigNames'), fileout)" in text


def test_progressive_authoring_api_matches_deployable_shape():
    director = MagicMock()
    prod = (
        Production("Demo.Production")
        .testing()
        .tracing()
        .actor_pool(3)
        .describe("Order ingestion")
        .in_namespace("IRISAPP")
        .with_director(director)
    )

    orders = prod.operation(OrderOperation).pool(4).trace()
    file = (
        prod.service("FileInput", FileService)
        .category_as("Inbound")
        .pool(2)
        .disable()
        .enable()
        .run_foreground()
        .trace()
        .schedule_on("*/5 * * * *")
        .comment_as("Read order files")
        .host_setting("Removed", "temporary")
        .host_setting("Removed", None)
        .host_settings_update({"Limit": 10})
        .setting("Mode", "test")
        .settings_update({"Mode": "prod"})
        .adapter_setting("Charset", "utf-8")
        .adapter_settings_update({"Timeout": 5})
        .other_setting("Custom", "Preserved", "yes")
        .connect("Output", orders)
    )

    assert file is prod.item("FileInput")
    assert prod.namespace == "IRISAPP"
    assert prod._director is director

    data = prod.to_dict()["Demo.Production"]
    file_item = data["Item"][1]
    settings = {
        (setting["@Target"], setting["@Name"]): setting["#text"]
        for setting in file_item["Setting"]
    }

    assert data["@TestingEnabled"] == "true"
    assert data["@LogGeneralTraceEvents"] == "true"
    assert data["ActorPoolSize"] == "3"
    assert data["Description"] == "Order ingestion"

    assert file_item["@Name"] == "FileInput"
    assert file_item["@Category"] == "Inbound"
    assert file_item["@PoolSize"] == "2"
    assert file_item["@Enabled"] == "true"
    assert file_item["@Foreground"] == "true"
    assert file_item["@LogTraceEvents"] == "true"
    assert file_item["@Schedule"] == "*/5 * * * *"
    assert file_item["@Comment"] == "Read order files"

    assert settings[("Host", "Limit")] == "10"
    assert settings[("Host", "Mode")] == "prod"
    assert settings[("Host", "Output")] == "OrderOperation"
    assert ("Host", "Removed") not in settings
    assert settings[("Adapter", "Charset")] == "utf-8"
    assert settings[("Adapter", "Timeout")] == "5"
    assert settings[("Custom", "Preserved")] == "yes"

    graph_edge = prod.graph().to_dict()["edges"][0]
    assert graph_edge["source"] == "FileInput.Output"
    assert graph_edge["target"] == "OrderOperation"


def test_progressive_component_connect_appends_fanout_targets():
    prod = Production("Demo.Production")
    first = prod.operation("FirstOrderOperation", OrderOperation)
    second = prod.operation("SecondOrderOperation", class_name="Demo.SecondOperation")

    file = (
        prod.service("FileInput", FileService)
        .connect("Output", first)
        .connect("Output", second, mode="add")
    )

    assert file.host_settings["Output"] == ("FirstOrderOperation,SecondOrderOperation")
    assert [edge.target for edge in prod.graph().edges] == [
        "FirstOrderOperation",
        "SecondOrderOperation",
    ]
    with pytest.raises(ValueError, match="ambiguous"):
        file.Output.resolve()


def test_production_connect_can_remove_one_or_all_targets():
    prod = Production("Demo.Production")
    first = prod.operation("FirstOrderOperation", OrderOperation)
    second = prod.operation("SecondOrderOperation", class_name="Demo.SecondOperation")
    file = prod.service("FileInput", FileService)
    prod.connect(file.Output, first)
    prod.connect(file.Output, second, mode="add")

    prod.connect(file.Output, first, mode="remove")

    assert file.host_settings["Output"] == "SecondOrderOperation"
    assert [edge.target for edge in prod.graph().edges] == ["SecondOrderOperation"]

    prod.connect(file.Output, mode="remove")

    assert "Output" not in file.host_settings
    assert prod.graph().edges == ()


def test_production_validate_warns_and_strict_raises_for_unknown_public_attr():
    prod = Production("Demo.Production")
    prod.unexpected = "value"

    with pytest.warns(ProductionValidationWarning, match="Unknown public"):
        report = prod.validate()

    assert report.has_issues is True
    assert report.issues[0].path == "production.unexpected"
    with pytest.raises(ProductionValidationError, match="production.unexpected"):
        prod.validate(strict=True)


def test_production_validate_warns_unknown_python_host_setting():
    prod = Production("Demo.Production")
    prod.service("FileInput", FileService, settings={"MissingSetting": "value"})

    with pytest.warns(ProductionValidationWarning, match="MissingSetting"):
        report = prod.validate()

    assert report.issues[0].path == "items.FileInput.settings.Host.MissingSetting"


def test_production_validate_reports_known_setting_alias_suggestion():
    class RoutingService(BusinessService):
        TargetConfigName = target()

    prod = Production("Demo.Production")
    prod.service(
        "FileInput",
        RoutingService,
        settings={"target_config_name": "OrderOperation"},
    )

    with pytest.warns(ProductionValidationWarning, match="Use 'TargetConfigName'"):
        report = prod.validate()

    assert report.issues[0].suggestion == "Use 'TargetConfigName'."


def test_production_validate_does_not_infer_arbitrary_snake_case_setting():
    class CustomSettingService(BusinessService):
        MySetting = "default"

    prod = Production("Demo.Production")
    prod.service(
        "FileInput",
        CustomSettingService,
        settings={"my_setting": "value"},
    )

    with pytest.warns(ProductionValidationWarning, match="Unknown setting"):
        report = prod.validate()

    assert report.issues[0].suggestion == ""


def test_production_validate_warns_unknown_python_adapter_setting():
    class ConfiguredAdapter(InboundAdapter):
        Port: int = 0

    class ConfiguredAdapterService(BusinessService):
        @staticmethod
        def get_adapter_type():
            return (
                f"Python.{ConfiguredAdapter.__module__}."
                "ConfiguredAdapter"
            ).replace("_", "")

    prod = Production("Demo.Production")
    prod.service(
        "Input",
        ConfiguredAdapterService,
        adapter_class=ConfiguredAdapter,
        adapter_settings={"MissingAdapterSetting": "value"},
    )

    with pytest.warns(ProductionValidationWarning, match="MissingAdapterSetting"):
        report = prod.validate()

    assert (
        report.issues[0].path
        == "items.Input.settings.Adapter.MissingAdapterSetting"
    )


def test_production_validate_warns_process_adapter_settings():
    class DemoProcess(BusinessProcess):
        pass

    prod = Production("Demo.Production")
    prod.process("Process", DemoProcess, adapter_settings={"Port": 1972})

    with pytest.warns(ProductionValidationWarning, match="do not support"):
        report = prod.validate()

    assert report.issues[0].path == "items.Process.settings.Adapter"


def test_component_ref_exposes_adapter_class_name_without_serializing_it():
    prod = Production("Demo.Production")
    service = prod.service("FileInput", FileService)

    assert service.adapter_class_name == "Ens.InboundAdapter"
    assert service.inspect(refresh=False)["adapter_class_name"] == "Ens.InboundAdapter"
    assert prod.graph().to_dict()["nodes"][0]["adapter_class_name"] == (
        "Ens.InboundAdapter"
    )
    assert "@AdapterClassName" not in prod.to_dict()["Demo.Production"]["Item"][0]


def test_component_ref_supports_python_adapter_class_registration(tmp_path):
    prod = Production("Demo.Production")
    service = prod.service(
        "Input",
        AdapterService,
        adapter_class=PythonInboundAdapter,
    )

    assert service.adapter_class is PythonInboundAdapter
    assert service.adapter_class_name == (
        f"Python.{PythonInboundAdapter.__module__}.PythonInboundAdapter".replace(
            "_",
            "",
        )
    )
    assert prod.adapter_registrations() == (service,)

    with patch.object(migration_utils, "register_component") as mock_register:
        with patch.object(migration_utils, "register_production_definition"):
            migration_utils.set_productions_settings([prod], str(tmp_path))

    assert mock_register.call_count == 2
    assert mock_register.call_args_list[1].args == (
        PythonInboundAdapter.__module__,
        "PythonInboundAdapter",
        str(tmp_path),
        1,
        service.adapter_class_name,
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
    director.list_productions.return_value = {"Demo.Production": {"Status": "Stopped"}}
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
        match=(
            "Cannot restart component 'OrderOperation' in production 'Demo.Production'"
        ),
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
    assert prod.item("FileInput").adapter_class_name == ""
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
            "source_target_setting": "TargetConfigNames",
            "target": "OrderOperation",
            "origin": "runtime",
            "interaction": "request",
            "runtime": True,
        }
    ]
    assert "FileInput [EnsLib.File.PassthroughService]" in str(graph)
    assert "TargetConfigNames -> OrderOperation" in str(graph)


def test_production_from_dict_falls_back_when_runtime_has_only_internal_targets():
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
            ],
        }
    }
    connections = {
        "items": [
            {"item": "FileInput", "connections": ["Ens.Alert"]},
            {"item": "OrderOperation", "connections": ["Ens.ScheduleHandler"]},
        ],
    }

    prod = Production.from_dict(exported, connections=connections)

    assert prod.graph().to_dict()["edges"] == [
        {
            "source": "FileInput.Output",
            "source_item": "FileInput",
            "source_target_setting": "Output",
            "target": "OrderOperation",
            "origin": "inferred",
            "interaction": "request",
            "metadata": {
                "source": "Host setting fallback",
                "reason": "runtime discovery returned no targets",
            },
            "inferred": True,
        }
    ]


def test_production_from_dict_infers_target_config_when_runtime_has_trace_target():
    exported = {
        "Demo.Production": {
            "Item": [
                {
                    "@Name": "InteropService",
                    "@ClassName": "HS.FHIRServer.Interop.Service",
                    "Setting": [
                        {
                            "@Target": "Host",
                            "@Name": "TargetConfigName",
                            "#text": "FHIR_MAIN",
                        },
                        {
                            "@Target": "Host",
                            "@Name": "TraceOperations",
                            "#text": "*FULL*",
                        },
                    ],
                },
                {
                    "@Name": "FHIR_MAIN",
                    "@ClassName": "Python.EAI.bp.FhirMainProcess",
                },
                {
                    "@Name": "HS.Util.Trace.Operations",
                    "@ClassName": "HS.Util.Trace.Operations",
                },
            ],
        }
    }
    connections = {
        "items": [
            {
                "item": "InteropService",
                "connections": ["Ens.Alert", "HS.Util.Trace.Operations"],
            },
        ],
    }

    prod = Production.from_dict(exported, connections=connections)

    assert prod.graph().to_dict()["edges"] == [
        {
            "source": "InteropService",
            "source_item": "InteropService",
            "source_target_setting": "",
            "target": "HS.Util.Trace.Operations",
            "origin": "runtime",
            "interaction": "request",
            "runtime": True,
        },
        {
            "source": "InteropService.TargetConfigName",
            "source_item": "InteropService",
            "source_target_setting": "TargetConfigName",
            "target": "FHIR_MAIN",
            "origin": "inferred",
            "interaction": "request",
            "metadata": {
                "source": "Host setting fallback",
                "reason": "runtime discovery did not report this target setting",
            },
            "inferred": True,
        },
    ]
    mermaid = prod.to_mermaid()
    assert (
        'node_InteropService -- "(runtime) | runtime" '
        "--> node_HS_Util_Trace_Operations"
    ) in mermaid
    assert (
        'node_InteropService -- "TargetConfigName | inferred" --> node_FHIR_MAIN'
    ) in mermaid


def test_production_from_dict_uses_runtime_adapter_metadata():
    exported = {
        "Demo.Production": {
            "Item": [
                {"@Name": "FileInput", "@ClassName": "Python.demo.FileService"},
                {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
            ]
        }
    }
    connections = {
        "items": [
            {
                "item": "FileInput",
                "adapter_class_name": "Ens.InboundAdapter",
                "connections": ["OrderOperation"],
            }
        ]
    }

    prod = Production.from_dict(exported, connections=connections)

    assert prod.get_component("FileInput").adapter_class_name == "Ens.InboundAdapter"
    assert prod.graph().to_dict()["nodes"][0]["adapter_class_name"] == (
        "Ens.InboundAdapter"
    )


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
                "metadata": {"source": "Host setting fallback"},
            }
        ],
        "after": [
            {
                "target": "OrderOperation",
                "origin": "authored",
                "interaction": "request",
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
    current.connect(current_file.target_setting("Output"), old_orders)

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


def test_production_plan_classifies_safe_and_blocked_operations():
    current = Production("Demo.Production")
    current_file = current.service(
        "FileInput",
        class_name="Demo.OldFileService",
        settings={"Limit": 5},
    )
    old_orders = current.operation("OldOrderOperation", class_name="Demo.OldOrders")
    current.connect(current_file.target_setting("Output"), old_orders)

    desired = Production("Demo.Production")
    desired_file = desired.service("FileInput", FileService, settings={"Limit": 10})
    orders = desired.operation(OrderOperation)
    desired.connect(desired_file.Output, orders)

    plan = desired.plan(current)
    by_path = {operation.path: operation for operation in plan.operations}

    assert by_path["items.OrderOperation"].op_type == "add_item"
    assert by_path["items.OrderOperation"].allowed_by_default is True
    assert by_path["items.FileInput.settings.Host.Limit"].op_type == "set_setting"
    assert by_path["items.FileInput.settings.Host.Limit"].risk == "safe"
    assert by_path["connections.FileInput.Output"].op_type == "set_route_setting"
    assert by_path["connections.FileInput.Output"].risk == "safe"
    assert by_path["items.OldOrderOperation"].op_type == "delete_item"
    assert by_path["items.OldOrderOperation"].requires_allow_destructive is True
    assert by_path["items.FileInput.class_name"].op_type == "replace_item_class"
    assert by_path["items.FileInput.class_name"].requires_allow_destructive is True


def test_production_plan_blocks_runtime_only_route_mutation():
    current = Production.from_dict(
        {
            "Demo.Production": {
                "Item": [
                    {"@Name": "Router", "@ClassName": "Demo.Router"},
                    {"@Name": "OrderOperation", "@ClassName": "Demo.OrderOperation"},
                ]
            }
        },
        connections={"items": [{"item": "Router", "connections": ["OrderOperation"]}]},
    )
    desired = Production("Demo.Production")
    desired.component("Router", class_name="Demo.Router")
    desired.operation("OrderOperation", class_name="Demo.OrderOperation")

    plan = desired.plan(current)
    operation = next(op for op in plan.operations if op.kind == "connection")

    assert operation.op_type == "set_route_setting"
    assert operation.risk == "unsupported"
    assert "no source setting" in operation.reason


def test_production_apply_uses_plan_not_full_sync(tmp_path):
    director = MagicMock()
    current = Production("Demo.Production")
    current.service("FileInput", FileService, settings={"Limit": 5})
    desired = Production("Demo.Production", director=director)
    desired.service("FileInput", FileService, settings={"Limit": 10})
    plan = desired.plan(current)
    safe_operation = next(op for op in plan.operations if op.allowed_by_default)
    director.export_production.return_value = current.to_dict()
    director.export_production_connections.return_value = {"items": []}
    director.export_production_queue_info.return_value = {"items": []}
    director.apply_production_plan.return_value = {
        "operations": [
            {
                "id": safe_operation.id,
                "op_type": safe_operation.op_type,
                "status": "applied",
            }
        ]
    }

    with patch.object(migration_utils, "set_productions_settings") as mock_sync:
        with patch.object(migration_utils, "_register_production_object_messages"):
            with patch.object(migration_utils, "_register_production_object_components"):
                result = desired.apply(plan, backup_dir=str(tmp_path), update=False)

    mock_sync.assert_not_called()
    director.apply_production_plan.assert_called_once()
    assert result.applied == 1
    assert (tmp_path / os.path.basename(result.backup_path) / "production.json").exists()
    assert (tmp_path / os.path.basename(result.backup_path) / "plan.json").exists()


def test_production_apply_fails_when_plan_fingerprint_is_stale(tmp_path):
    director = MagicMock()
    current = Production("Demo.Production")
    current.service("FileInput", FileService, settings={"Limit": 5})
    changed_current = Production("Demo.Production")
    changed_current.service("FileInput", FileService, settings={"Limit": 7})
    desired = Production("Demo.Production", director=director)
    desired.service("FileInput", FileService, settings={"Limit": 10})
    plan = desired.plan(current)
    director.export_production.return_value = changed_current.to_dict()
    director.export_production_connections.return_value = {"items": []}
    director.export_production_queue_info.return_value = {"items": []}

    with pytest.raises(RuntimeError, match="changed since the plan was created"):
        desired.apply(plan, backup_dir=str(tmp_path), update=False)

    director.apply_production_plan.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_production_verify_reports_safe_convergence_and_residual_blocked_ops():
    current = Production("Demo.Production")
    current.service("FileInput", class_name="Demo.Old", settings={"Limit": 5})
    desired = Production("Demo.Production")
    desired.service("FileInput", class_name="Demo.Old", settings={"Limit": 10})
    desired.operation("NewOperation", class_name="Demo.NewOperation")
    plan = desired.plan(current)
    director = MagicMock()
    desired.with_director(director)
    director.export_production.return_value = desired.to_dict()
    director.export_production_connections.return_value = {"items": []}

    result = desired.verify(plan)

    assert result.success is True
    assert len(result.converged_operations) == len(plan.safe_operations)
    assert result.residual_operations == ()


def test_production_rollback_requires_destructive_approval(tmp_path):
    with pytest.raises(RuntimeError, match="requires allow_destructive"):
        Production.rollback_backup(str(tmp_path), allow_destructive=False)


def test_production_rollback_normalizes_named_backup_export(tmp_path):
    backup = tmp_path / "backup"
    backup.mkdir()
    production_data = Production("Demo.Production").to_dict()
    (backup / "production.json").write_text(json.dumps(production_data), encoding="utf-8")
    (backup / "metadata.json").write_text(
        json.dumps(
            {
                "production": "Demo.Production",
                "namespace": "USER",
                "plan_id": "plan-1",
            }
        ),
        encoding="utf-8",
    )
    director = MagicMock()
    director.status_production.return_value = {
        "Production": "Other.Production",
        "Status": "stopped",
    }
    director.export_production.return_value = production_data
    director.export_production_connections.return_value = {"items": []}

    with patch.object(
        migration_utils,
        "register_production_definition",
    ) as mock_register:
        result = Production.rollback_backup(
            str(backup),
            director=director,
            allow_destructive=True,
            update=False,
        )

    mock_register.assert_called_once_with(
        "Demo.Production",
        {"Production": production_data["Demo.Production"]},
    )
    assert result.converged_operations == ("rollback",)


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


def test_production_from_dict_infers_when_runtime_discovery_returns_no_targets():
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

    assert prod.resolve_target("Router.TargetConfigNames") == "OrderOperation"
    assert prod.graph().to_dict()["edges"] == [
        {
            "source": "Router.TargetConfigNames",
            "source_item": "Router",
            "source_target_setting": "TargetConfigNames",
            "target": "OrderOperation",
            "origin": "inferred",
            "interaction": "request",
            "metadata": {
                "source": "Host setting fallback",
                "reason": "runtime discovery returned no targets",
            },
            "inferred": True,
        }
    ]


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
            "source_target_setting": "",
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
        "items": [
            {
                "item": "FileInput",
                "adapter_class_name": "Ens.InboundAdapter",
                "connections": ["OrderOperation"],
            }
        ]
    }

    prod = Production.from_iris("Demo.Production", director=director)

    director.export_production.assert_called_once_with("Demo.Production")
    director.export_production_connections.assert_called_once_with("Demo.Production")
    assert prod.item("FileInput").Output.resolve() == "OrderOperation"
    assert prod.get_component("FileInput").adapter_class_name == "Ens.InboundAdapter"


def test_objectscript_component_uses_class_name_and_manual_port():
    prod = Production("Demo.Production")
    file = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
    output = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

    prod.connect(file.target_setting("TargetConfigNames"), output)

    assert prod.to_dict()["Demo.Production"]["Item"][0]["@ClassName"] == (
        "EnsLib.File.PassthroughService"
    )
    assert prod.component_registrations() == ()
    assert prod.resolve_target("FileIn.TargetConfigNames") == "FileOut"


def test_component_crud_edits_python_graph_only():
    prod = Production("Demo.Production")
    file = prod.add_component("FileIn", class_name="EnsLib.File.PassthroughService")
    op = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")
    prod.connect(file.target_setting("TargetConfigNames"), op)

    prod.update_component("FileIn", settings={"Limit": 10}, enabled=False)
    assert prod.item("FileIn").host_settings["Limit"] == 10
    assert prod.item("FileIn").enabled is False

    prod.disconnect("FileIn.TargetConfigNames")
    assert "TargetConfigNames" not in prod.item("FileIn").host_settings
    assert prod.graph().to_dict()["edges"] == []

    prod.connect(file.target_setting("TargetConfigNames"), op)
    prod.delete_component("FileOut")

    assert prod.graph().to_dict()["edges"] == []
    with pytest.raises(ValueError, match="does not exist"):
        prod.item("FileOut")


def test_production_sync_registers_current_definition():
    prod = Production("Demo.Production")
    prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

    with patch.object(migration_utils, "set_productions_settings") as mock_set:
        with patch("iop.runtime.local._LocalDirector.update_production") as mock_update:
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
        migration_utils,
        "set_productions_settings",
        side_effect=capture_namespace,
    ):
        with patch("iop.runtime.local._LocalDirector.update_production"):
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

    with patch("iop.runtime.remote.get_remote_settings", return_value=None):
        with patch(
            "iop.runtime.local._LocalDirector.status_production",
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

    with patch.object(migration_utils, "register_component") as mock_register:
        with patch.object(
            migration_utils, "register_production_definition"
        ) as mock_prod:
            migration_utils.set_productions_settings(production_list, str(tmp_path))

    assert production_list == original
    mock_register.assert_called_once()
    mock_prod.assert_called_once()


def test_set_productions_settings_supports_mixed_legacy_and_objects(tmp_path):
    legacy = {"Legacy.Production": {"Item": []}}
    prod = Production("Object.Production")
    prod.operation(OrderOperation)

    with patch.object(migration_utils, "register_component") as mock_register:
        with patch.object(
            migration_utils, "register_production_definition"
        ) as mock_prod:
            migration_utils.set_productions_settings([legacy, prod], str(tmp_path))

    mock_register.assert_called_once_with(
        OrderOperation.__module__,
        "OrderOperation",
        str(tmp_path),
        1,
        f"Python.{OrderOperation.__module__}.OrderOperation".replace("_", ""),
    )
    assert mock_prod.call_count == 2


def test_set_productions_settings_strict_validation_fails_before_registration(tmp_path):
    prod = Production("Object.Production")
    prod.operation(OrderOperation, settings={"MissingSetting": "value"})

    with patch.object(migration_utils, "register_component"):
        with patch.object(migration_utils, "register_production_definition") as mock_prod:
            with pytest.raises(ProductionValidationError, match="MissingSetting"):
                migration_utils.set_productions_settings(
                    [prod],
                    str(tmp_path),
                    strict_production_validation=True,
                )

    mock_prod.assert_not_called()


def test_migration_plan_lists_production_objects_and_auto_components():
    prod = Production("Object.Production")
    prod.operation(OrderOperation)

    class Settings:
        CLASSES = {}
        PRODUCTIONS = [prod]

    plan = migration_utils._build_migration_plan(Settings, ".")

    assert "Object.Production" in plan["productions"]
    assert (
        f"Python.{OrderOperation.__module__}.OrderOperation".replace("_", "")
        + f" -> {OrderOperation.__module__}.OrderOperation (component)"
        in plan["classes"]
    )


def test_migration_plan_reports_production_validation_issues():
    prod = Production("Object.Production")
    prod.operation(OrderOperation, settings={"MissingSetting": "value"})

    class Settings:
        CLASSES = {}
        PRODUCTIONS = [prod]

    plan = migration_utils._build_migration_plan(Settings, ".")

    assert any("MissingSetting" in issue for issue in plan["validation"])
    with pytest.raises(ProductionValidationError, match="MissingSetting"):
        migration_utils._build_migration_plan(
            Settings,
            ".",
            strict_production_validation=True,
        )


def test_migration_plan_reports_unknown_legacy_production_keys():
    class Settings:
        CLASSES = {}
        PRODUCTIONS = [{"Legacy.Production": {"Unexpected": "value"}}]

    plan = migration_utils._build_migration_plan(Settings, ".")

    assert any("Unexpected" in issue for issue in plan["validation"])


def test_migration_plan_lists_production_persistent_messages():
    prod = Production("Object.Production")
    prod.message("Demo.Msg.NativeOrderMessage", NativeOrderMessage)

    class Settings:
        CLASSES = {}
        PRODUCTIONS = [prod]

    plan = migration_utils._build_migration_plan(Settings, ".")

    assert "Object.Production" in plan["productions"]
    assert (
        "Demo.Msg.NativeOrderMessage"
        + f" -> {NativeOrderMessage.__module__}.NativeOrderMessage "
        "(PersistentMessage)" in plan["classes"]
    )


def test_production_object_auto_registration_deduplicates_shared_classes(tmp_path):
    prod = Production("Object.Production")
    prod.operation(
        "FirstOrderOperation",
        OrderOperation,
        class_name="Python.SharedOrderOperation",
    )
    prod.operation(
        "SecondOrderOperation",
        OrderOperation,
        class_name="Python.SharedOrderOperation",
    )

    class Settings:
        CLASSES = {}
        PRODUCTIONS = [prod]

    plan = migration_utils._build_migration_plan(Settings, ".")
    assert (
        plan["classes"].count(
            "Python.SharedOrderOperation"
            + f" -> {OrderOperation.__module__}.OrderOperation (component)"
        )
        == 1
    )

    with patch.object(migration_utils, "register_component") as mock_register:
        with patch.object(migration_utils, "register_production_definition"):
            migration_utils.set_productions_settings([prod], str(tmp_path))

    mock_register.assert_called_once_with(
        OrderOperation.__module__,
        "OrderOperation",
        str(tmp_path),
        1,
        "Python.SharedOrderOperation",
    )


def test_business_host_request_helpers_resolve_target_setting_refs():
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


def test_business_process_send_request_async_resolves_target_setting_refs():
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
