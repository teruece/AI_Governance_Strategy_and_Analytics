"""Run a bounded planner over explicitly registered, read-only tools."""

from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass(frozen=True)
class Call:
    name: str
    arguments: dict


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    execute: Callable[[dict], dict]

    def output_schema(self) -> dict:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }

    def accepts(self, arguments: dict) -> bool:
        properties = self.parameters["properties"]
        return set(arguments) == set(properties) and all(
            isinstance(arguments[name], str)
            and ("enum" not in rule or arguments[name] in rule["enum"])
            for name, rule in properties.items()
        )


class PlannerError(Exception):
    """A planner returned an invalid response or could not finish."""


class Planner(Protocol):
    def next_call(self) -> Call | None: ...

    def accept(self, result: dict) -> None: ...


class ScriptedPlanner:
    def __init__(self, calls: tuple[Call, ...]):
        self.calls = iter(calls)

    def next_call(self) -> Call | None:
        return next(self.calls, None)

    def accept(self, result: dict) -> None:
        pass


def run(
    tools: tuple[Tool, ...],
    planner: Planner,
    render: Callable[[dict[str, dict]], dict],
    *,
    max_turns: int = 4,
) -> dict:
    allowed = {tool.name: tool for tool in tools}
    evidence: dict[str, dict] = {}
    trace: list[dict] = []

    def stopped(reason: str) -> dict:
        return {"status": "STOPPED", "reason": reason, "trace": trace}

    for _ in range(max_turns):
        try:
            call = planner.next_call()
        except PlannerError as error:
            return stopped(str(error))

        if call is None:
            return {
                "status": "COMPLETE",
                "report": render(evidence),
                "trace": trace,
            }

        tool = allowed.get(call.name)
        if tool is None:
            return stopped("UNKNOWN_TOOL")
        if tool.name in evidence:
            return stopped("REPEATED_TOOL")
        if not isinstance(call.arguments, dict) or not tool.accepts(call.arguments):
            return stopped("INVALID_ARGUMENTS")

        try:
            result = tool.execute(call.arguments)
        except ValueError:
            return stopped("TOOL_REJECTED_ARGUMENTS")

        evidence[tool.name] = result
        trace.append({"tool": tool.name, "arguments": call.arguments})
        planner.accept(result)

    return stopped("TURN_LIMIT")
