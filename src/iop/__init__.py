from iop.components.business_operation import _BusinessOperation
from iop.components.business_process import _BusinessProcess
from iop.components.business_service import _BusinessService
from iop.components.inbound_adapter import _InboundAdapter
from iop.components.outbound_adapter import _OutboundAdapter
from iop.components.polling_business_service import _PollingBusinessServiceMixin
from iop.components.private_session_duplex import _PrivateSessionDuplex
from iop.components.private_session_process import _PrivateSessionProcess
from iop.components.settings import Category as Category
from iop.components.settings import Setting as Setting
from iop.components.settings import controls as controls
from iop.components.settings import setting as setting
from iop.messages.base import (
    _Message,
    _PickleMessage,
    _PydanticMessage,
    _PydanticPickleMessage,
)
from iop.messages.decorators import handler as handler
from iop.messages.persistent import Field as Field
from iop.messages.persistent import Model as Model
from iop.messages.persistent import _PersistentMessage
from iop.migration.utils import _Utils
from iop.migration.utils import bind_component as bind_component
from iop.migration.utils import list_bindings as list_bindings
from iop.migration.utils import register_component as register_component
from iop.migration.utils import unbind_component as unbind_component
from iop.migration.utils import unregister_component as unregister_component
from iop.production import ComponentItem as ComponentItem
from iop.production import ComponentRef as ComponentRef
from iop.production import OperationItem as OperationItem
from iop.production import ProcessItem as ProcessItem
from iop.production import Production as Production
from iop.production import ProductionApplyResult as ProductionApplyResult
from iop.production import ProductionChangePlan as ProductionChangePlan
from iop.production import ProductionDiff as ProductionDiff
from iop.production import ProductionDiffEntry as ProductionDiffEntry
from iop.production import ProductionGraph as ProductionGraph
from iop.production import ProductionPlanOperation as ProductionPlanOperation
from iop.production import ProductionValidationError as ProductionValidationError
from iop.production import ProductionValidationIssue as ProductionValidationIssue
from iop.production import ProductionValidationReport as ProductionValidationReport
from iop.production import ProductionValidationWarning as ProductionValidationWarning
from iop.production import ProductionVerifyResult as ProductionVerifyResult
from iop.production import Route as Route
from iop.production import ServiceItem as ServiceItem
from iop.production import TargetSetting as TargetSetting
from iop.production import TargetSettingRef as TargetSettingRef
from iop.production import target as target
from iop.runtime.director import _Director
from iop.runtime.protocol import DirectorProtocol as DirectorProtocol

__all__ = [
    "BusinessOperation",
    "BusinessProcess",
    "BusinessService",
    "Category",
    "ComponentItem",
    "ComponentRef",
    "Director",
    "DirectorProtocol",
    "DuplexOperation",
    "DuplexProcess",
    "DuplexService",
    "Field",
    "InboundAdapter",
    "Message",
    "Model",
    "OperationItem",
    "OutboundAdapter",
    "PersistentMessage",
    "PickleMessage",
    "PollingBusinessService",
    "ProcessItem",
    "Production",
    "ProductionApplyResult",
    "ProductionChangePlan",
    "ProductionDiff",
    "ProductionDiffEntry",
    "ProductionGraph",
    "ProductionPlanOperation",
    "ProductionVerifyResult",
    "ProductionValidationError",
    "ProductionValidationIssue",
    "ProductionValidationReport",
    "ProductionValidationWarning",
    "PydanticMessage",
    "PydanticPickleMessage",
    "Route",
    "ServiceItem",
    "Setting",
    "TargetSetting",
    "TargetSettingRef",
    "Utils",
    "bind_component",
    "controls",
    "handler",
    "list_bindings",
    "register_component",
    "setting",
    "target",
    "unbind_component",
    "unregister_component",
]


class Utils(_Utils):
    pass


class InboundAdapter(_InboundAdapter):
    pass


class OutboundAdapter(_OutboundAdapter):
    pass


class BusinessService(_BusinessService):
    """Purpose:
        Inbound production entry point for messages entering an IoP production.

    Use when:
        External data, an adapter, or custom code must send a message into the
        production graph.

    Lifecycle:
        IRIS calls on_process_input(); the default implementation delegates the
        incoming request to on_message(request).

    Best practices:
        Declare outbound routes with target() and wire them in a Production
        graph. Use PollingBusinessService for scheduled Python polling.

    Common mistakes:
        Do not put startup work in __init__(); use on_init(). Do not instantiate
        downstream components directly.

    Minimal example:
        class FileIn(BusinessService):
            Output = target()

            def on_process_input(self, request):
                self.send_request_async(self.Output, request)

    Related:
        docs/cookbooks/add-polling-service.md,
        docs/cookbooks/hl7v2-native-input.md
    """

    pass


class PollingBusinessService(_PollingBusinessServiceMixin, BusinessService):
    """Purpose:
        Scheduled Python service called by the default IRIS inbound adapter.

    Use when:
        A production must poll an API, directory, queue, database, or other
        source from Python.

    Lifecycle:
        IRIS calls on_process_input(); the mixin delegates that call to
        on_poll().

    Best practices:
        Put one polling cycle in on_poll(). Declare outbound routes with
        target() and send messages with send_request_async(...).

    Common mistakes:
        Do not block forever inside on_poll(). Do not put startup work in
        __init__(); use on_init().

    Minimal example:
        class ApiPoller(PollingBusinessService):
            Output = target()

            def on_poll(self):
                self.send_request_async(self.Output, MyRequest())

    Related:
        docs/cookbooks/add-polling-service.md
    """

    pass


class BusinessOperation(_BusinessOperation):
    """Purpose:
        Outbound side-effect boundary for production messages.

    Use when:
        A production must call an external API, write a file, update a database,
        submit FHIR resources, or perform another side effect.

    Lifecycle:
        IRIS calls on_message(request). IoP can dispatch to @handler methods,
        typed one-argument methods, or the on_message fallback.

    Best practices:
        Keep external-system code here. Return a response message when callers
        expect synchronous results.

    Common mistakes:
        Do not put routing orchestration in an operation when a BusinessProcess
        should own the decision.

    Minimal example:
        class SubmitOrder(BusinessOperation):
            def on_message(self, request):
                return SubmitResult(ok=True)

    Related:
        docs/cookbooks/add-business-operation.md
    """

    pass


class BusinessProcess(_BusinessProcess):
    """Purpose:
        Routing, orchestration, decision, and transformation component.

    Use when:
        A production needs branching, enrichment, transformation, fan-out,
        request/reply orchestration, or response aggregation.

    Lifecycle:
        IRIS calls on_message(request). For async requests, IRIS can later call
        on_response(...) and on_complete(...).

    Best practices:
        Declare outbound routes with target() and wire them with
        Production.connect(...). Use @handler(MessageType) or typed methods for
        multiple message types.

    Common mistakes:
        Do not hard-code target component names when target() can expose a
        configurable route.

    Minimal example:
        class Router(BusinessProcess):
            Accepted = target()

            def on_message(self, request):
                return self.send_request_sync(self.Accepted, request)

    Related:
        docs/cookbooks/add-business-process.md,
        docs/cookbooks/production-settings-and-targets.md
    """

    pass


class DuplexService(_PrivateSessionDuplex):
    pass


class DuplexOperation(_PrivateSessionDuplex):
    pass


class DuplexProcess(_PrivateSessionProcess):
    pass


class Message(_Message):
    """Purpose:
        Python-only JSON-serialized message contract.

    Use when:
        IoP components exchange structured Python data and IRIS does not need a
        native persistent message body.

    Lifecycle:
        IoP serializes dataclass fields into IOP.Message and restores the Python
        class on receipt.

    Best practices:
        Decorate subclasses with @dataclass. Use PydanticMessage when runtime
        validation is more important.

    Common mistakes:
        Do not use Message without @dataclass. Do not register Message classes
        in CLASSES; use PersistentMessage for native IRIS message bodies.

    Minimal example:
        @dataclass
        class OrderRequest(Message):
            order_id: str

    Related:
        docs/cookbooks/add-business-process.md,
        docs/cookbooks/add-business-operation.md,
        docs/getting-started/register-component.md
    """

    pass


class PickleMessage(_PickleMessage):
    """Python-only pickle-serialized message contract.

    Prefer Message or PydanticMessage for new app code unless JSON-compatible
    fields cannot represent the payload.
    """

    pass


class PydanticMessage(_PydanticMessage):
    """Python-only Pydantic message contract with validation.

    Use for app messages that benefit from Pydantic validation. Do not decorate
    PydanticMessage classes with @dataclass and do not put these classes in
    CLASSES; see docs/getting-started/register-component.md.
    """

    pass


class PydanticPickleMessage(_PydanticPickleMessage):
    """Pydantic message contract serialized through pickle.

    Prefer PydanticMessage unless the payload must preserve Python-only object
    shapes that JSON serialization cannot represent.
    """

    pass


class PersistentMessage(_PersistentMessage):
    """Native persistent IRIS message body contract.

    Use when IRIS needs a generated message class or persistent message body.
    Prefer Message or PydanticMessage for Python-only routing. See
    docs/getting-started/register-component.md and docs/settings.md.
    """

    _iop_persistent_message_abstract = True


class Director(_Director):
    pass
