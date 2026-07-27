from typing import Any

from app.tools.mcp.schema_builder import BookingRequest

RECORDED_BOOKING_REQUESTS: list[dict[str, str]] = []


async def execute_booking(
    arguments: dict[str, Any] | BookingRequest,
) -> dict[str, Any]:
    booking = (
        arguments
        if isinstance(arguments, BookingRequest)
        else BookingRequest.model_validate(arguments)
    )
    details = booking.model_dump()
    RECORDED_BOOKING_REQUESTS.append(details.copy())
    return {
        "status": "recorded",
        "tool": "request_booking",
        "booking": details,
        "calendar_connected": False,
    }


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "request_booking":
        return await execute_booking(arguments)
    return {"status": "error", "tool": tool_name, "error": "unsupported_tool"}


def clear_recorded_bookings() -> None:
    RECORDED_BOOKING_REQUESTS.clear()
