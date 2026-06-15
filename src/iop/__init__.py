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
    """Inbound production entry point.

    Use for message-driven services or Python services that receive data and
    send messages into a production. For polling services, prefer
    PollingBusinessService. For task recipes, see
    docs/cookbooks/add-polling-service.md and docs/cookbooks/hl7v2-native-input.md.
    """

    pass


class PollingBusinessService(_PollingBusinessServiceMixin, BusinessService):
    """Scheduled inbound service called by the default IRIS inbound adapter.

    Declare outbound routes with target() and send messages with
    send_request_async(...). Do not put startup work in __init__(); use
    on_init(). See docs/cookbooks/add-polling-service.md.
    """

    pass


class BusinessOperation(_BusinessOperation):
    """Outbound side-effect boundary for production messages.

    Use operations for external APIs, file writes, database writes, FHIR
    submission, and other side effects. Dispatch can use on_message(), typed
    one-argument methods, or @handler(MessageType). See
    docs/cookbooks/add-business-operation.md.
    """

    pass


class BusinessProcess(_BusinessProcess):
    """Routing, orchestration, decision, and transformation component.

    Declare outbound routes with target() and connect them in a Production
    graph. Dispatch can use on_message(), typed one-argument methods, or
    @handler(MessageType). See docs/cookbooks/add-business-process.md.
    """

    pass


class DuplexService(_PrivateSessionDuplex):
    pass


class DuplexOperation(_PrivateSessionDuplex):
    pass


class DuplexProcess(_PrivateSessionProcess):
    pass


class Message(_Message):
    """Python-only JSON-serialized message contract.

    Use @dataclass for ordinary app messages between IoP components. Prefer
    PersistentMessage only when IRIS needs a native persistent message body. See
    docs/cookbooks/add-business-process.md and
    docs/cookbooks/add-business-operation.md.
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
