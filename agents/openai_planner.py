"""Optional Responses API planner. The runtime controls actual tool execution."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .runtime import Call, PlannerError, Tool


ENDPOINT = "https://api.openai.com/v1/responses"
MAX_RESPONSE_BYTES = 256 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def fetch_response(payload: dict, api_key: str) -> dict:
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        raise PlannerError(f"PROVIDER_HTTP_{error.code}") from None
    except (URLError, OSError):
        raise PlannerError("PROVIDER_UNREACHABLE") from None

    if len(body) > MAX_RESPONSE_BYTES:
        raise PlannerError("PROVIDER_RESPONSE_TOO_LARGE")

    try:
        return json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise PlannerError("PROVIDER_INVALID_JSON") from None


class OpenAIPlanner:
    def __init__(
        self,
        tools: tuple[Tool, ...],
        instructions: str,
        question: str,
        model: str,
        api_key: str,
        *,
        transport=fetch_response,
    ):
        self.instructions = (
            "Choose which supplied read-only tool to call to investigate the scenario. "
            "When sufficient evidence is collected or the input is blocked, stop calling tools. "
            "The application renders the final report. "
            + instructions
        )
        self.input = [{"role": "user", "content": question}]
        self.tools = [tool.output_schema() for tool in tools]
        self.model = model
        self.api_key = api_key
        self.transport = transport
        self.call_id: str | None = None

    def next_call(self) -> Call | None:
        response = self.transport(
            {
                "model": self.model,
                "input": self.input.copy(),
                "instructions": self.instructions,
                "tools": self.tools,
                "parallel_tool_calls": False,
                "store": False,
                "include": ["reasoning.encrypted_content"],
                "max_output_tokens": 1200,
            },
            self.api_key,
        )
        if not isinstance(response, dict) or response.get("status") != "completed":
            raise PlannerError("PROVIDER_INCOMPLETE_RESPONSE")

        allowed_types = {"function_call", "message", "reasoning"}
        output = response.get("output")
        if not isinstance(output, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("type"), str)
            or item["type"] not in allowed_types
            for item in output
        ):
            raise PlannerError("PROVIDER_INVALID_OUTPUT")

        calls = [item for item in output if item["type"] == "function_call"]
        if not calls:
            return None
        if len(calls) != 1:
            raise PlannerError("PROVIDER_MULTIPLE_CALLS")

        call = calls[0]
        self.call_id = call.get("call_id")
        name = call.get("name")
        raw_arguments = call.get("arguments")
        if not all(isinstance(value, str) and value for value in (self.call_id, name, raw_arguments)):
            raise PlannerError("PROVIDER_INVALID_CALL")

        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            raise PlannerError("PROVIDER_INVALID_ARGUMENTS") from None

        if not isinstance(arguments, dict):
            raise PlannerError("PROVIDER_INVALID_ARGUMENTS")

        self.input.extend(output)
        return Call(name, arguments)

    def accept(self, result: dict) -> None:
        self.input.append(
            {
                "type": "function_call_output",
                "call_id": self.call_id,
                "output": json.dumps(result),
            }
        )
