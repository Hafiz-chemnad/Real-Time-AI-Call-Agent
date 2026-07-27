from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class BookingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service: str
    date: str
    time: str

    @field_validator("service", "date", "time", mode="before")
    @classmethod
    def non_empty_text(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("booking fields must be non-empty strings")
        return " ".join(value.split())


def build_booking_tool_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "request_booking",
            "description": "Record an appointment booking request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                },
                "required": ["service", "date", "time"],
                "additionalProperties": False,
            },
        },
    }


def build_tool_schemas() -> list[dict[str, Any]]:
    return [build_booking_tool_schema()]
