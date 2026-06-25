import os
import re
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


load_dotenv(Path(__file__).with_name(".env"), override=True)


CaseType = Literal[
    "wrong_transfer",
    "payment_failed",
    "refund_request",
    "phishing_or_social_engineering",
    "other",
]
Severity = Literal["low", "medium", "high", "critical"]
Department = Literal[
    "customer_support",
    "dispute_resolution",
    "payments_ops",
    "fraud_risk",
]


class TicketRequest(BaseModel):
    ticket_id: str
    channel: str
    locale: str
    message: str


class TicketClassification(BaseModel):
    ticket_id: str = Field(description="Must match the input ticket_id exactly.")
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str = Field(
        description="One or two neutral sentences for a support agent."
    )
    human_review_required: bool
    confidence: float = Field(ge=0, le=1)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
structured_llm = (
    llm.with_structured_output(TicketClassification, method="json_schema")
    if llm
    else None
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You classify digital finance support tickets.

Return only the requested structured output.

Rules:
- case_type must be one of: wrong_transfer, payment_failed, refund_request,
  phishing_or_social_engineering, other.
- severity must be one of: low, medium, high, critical.
- department must be one of: customer_support, dispute_resolution,
  payments_ops, fraud_risk.
- Route wrong_transfer to dispute_resolution.
- Route payment_failed to payments_ops.
- Route phishing_or_social_engineering to fraud_risk.
- Route other and low severity refund_request to customer_support.
- Set human_review_required to true for high severity, critical severity, or phishing cases.
- Keep agent_summary neutral and short.
- Never ask the customer to share PIN, OTP, password, or full card number.
""",
        ),
        (
            "human",
            """
            Ticket:
            ticket_id: {ticket_id}
            channel: {channel}
            locale: {locale}
            message: {message}
            """,
        ),
    ]
)

ticket_chain = prompt | structured_llm if structured_llm else None


def classify_ticket(ticket: TicketRequest) -> TicketClassification:
    if not ticket_chain:
        raise RuntimeError("OPENAI_API_KEY is required to classify tickets with the LLM.")

    result = ticket_chain.invoke(ticket.model_dump())
    if isinstance(result, dict):
        result = TicketClassification(**result)
    return _enforce_response_rules(ticket, result)


def _enforce_response_rules(
    ticket: TicketRequest, result: TicketClassification
) -> TicketClassification:
    result.ticket_id = ticket.ticket_id

    if result.case_type == "phishing_or_social_engineering":
        result.department = "fraud_risk"
        result.human_review_required = True

    if result.severity in ["high", "critical"]:
        result.human_review_required = True

    result.agent_summary = _safe_summary(result.agent_summary)
    result.confidence = max(0, min(1, result.confidence))
    return result


def _safe_summary(summary: str) -> str:
    unsafe_request = re.search(
        r"\b(share|send|provide|tell|give)\b.{0,40}\b(pin|otp|password|full card)\b",
        summary,
        flags=re.IGNORECASE,
    )
    if unsafe_request:
        return "Customer submitted a support request that needs human review."
    return summary
