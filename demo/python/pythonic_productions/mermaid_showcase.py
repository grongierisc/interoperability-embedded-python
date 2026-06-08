from dataclasses import dataclass

from iop import (
    BusinessOperation,
    BusinessProcess,
    BusinessService,
    Message,
    PollingBusinessService,
    Production,
    target,
)


@dataclass
class ClaimReceived(Message):
    claim_id: str = ""


@dataclass
class ClaimValidated(Message):
    claim_id: str = ""


@dataclass
class FraudScoreRequest(Message):
    claim_id: str = ""


@dataclass
class FraudScore(Message):
    score: int = 0


@dataclass
class ClaimApproved(Message):
    claim_id: str = ""


@dataclass
class ClaimRejected(Message):
    claim_id: str = ""


@dataclass
class PaymentResult(Message):
    accepted: bool = False


@dataclass
class NotificationRequest(Message):
    claim_id: str = ""


@dataclass
class AuditEvent(Message):
    event_id: str = ""


class ClaimApiService(BusinessService):
    IncomingClaims = target()


class ClaimFileService(PollingBusinessService):
    IncomingClaims = target()


class ClaimValidationProcess(BusinessProcess):
    ValidClaims = target()
    FraudChecks = target()
    RejectedClaims = target()


class ClaimDecisionProcess(BusinessProcess):
    Payment = target()
    Notification = target()
    Audit = target()


class FraudScoreOperation(BusinessOperation):
    pass


class PaymentGatewayOperation(BusinessOperation):
    pass


class NotificationOperation(BusinessOperation):
    pass


class AuditStoreOperation(BusinessOperation):
    pass


prod = Production("Demo.MermaidShowcaseProduction", testing_enabled=True)

api = prod.service("Claim API", ClaimApiService)
file_drop = prod.service("Claim File Drop", ClaimFileService)
validation = prod.process("Validate Claim", ClaimValidationProcess)
decision = prod.process("Route Claim Decision", ClaimDecisionProcess)
fraud = prod.operation("Fraud Score", FraudScoreOperation)
payment = prod.operation("Payment Gateway", PaymentGatewayOperation)
notification = prod.operation("Notification Sender", NotificationOperation)
audit = prod.operation("Audit Store", AuditStoreOperation)

prod.connect(api.IncomingClaims, validation)
prod.connect(file_drop.IncomingClaims, validation)
prod.connect(validation.FraudChecks, fraud)
prod.connect(validation.ValidClaims, decision)
prod.connect(validation.RejectedClaims, notification)
prod.connect(decision.Payment, payment)
prod.connect(decision.Notification, notification)
prod.connect(decision.Audit, audit)

PRODUCTIONS = [prod]


if __name__ == "__main__":
    print(prod.to_mermaid(), end="")
