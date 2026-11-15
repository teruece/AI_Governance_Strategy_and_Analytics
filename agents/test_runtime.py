import json
import unittest

from . import kpi, quality
from .openai_planner import OpenAIPlanner
from .runtime import Call, ScriptedPlanner, run


def provider_call(name, arguments, call_id):
    return {
        "status": "completed",
        "output": [{
            "type": "function_call",
            "name": name,
            "arguments": json.dumps(arguments),
            "call_id": call_id,
        }],
    }


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tools = kpi.tools("normal")
        self.calls = kpi.script("normal")

    def replay(self, calls, **kwargs):
        return run(self.tools, ScriptedPlanner(tuple(calls)), kpi.render, **kwargs)

    def test_unknown_tool_cannot_execute(self):
        outcome = self.replay([Call("publish_commentary", {})])
        self.assertEqual(outcome, {"status": "STOPPED", "reason": "UNKNOWN_TOOL", "trace": []})

    def test_scope_and_extra_fields_are_rejected(self):
        valid = self.calls[0].arguments
        for arguments in ({**valid, "current_period": "2026-11"}, {**valid, "sql": "DROP TABLE"}):
            with self.subTest(arguments=arguments):
                outcome = self.replay([Call(self.calls[0].name, arguments)])
                self.assertEqual(outcome["reason"], "INVALID_ARGUMENTS")
                self.assertEqual(outcome["trace"], [])

    def test_repeated_call_stops_without_rendering(self):
        outcome = self.replay([self.calls[0], self.calls[0]])
        self.assertEqual(outcome["reason"], "REPEATED_TOOL")
        self.assertEqual(len(outcome["trace"]), 1)
        self.assertNotIn("report", outcome)

    def test_turn_budget_includes_final_planner_response(self):
        outcome = self.replay(self.calls, max_turns=2)
        self.assertEqual(outcome["reason"], "TURN_LIMIT")
        self.assertNotIn("report", outcome)

    def test_early_model_stop_yields_insufficient_evidence(self):
        outcome = self.replay([])
        self.assertEqual(outcome["report"]["status"], "INSUFFICIENT_EVIDENCE")


class ProviderTests(unittest.TestCase):
    def test_tool_results_return_to_planner_but_model_prose_cannot_enter_report(self):
        calls = kpi.script("normal")
        responses = iter([
            provider_call(calls[0].name, calls[0].arguments, "call_1"),
            provider_call(calls[1].name, calls[1].arguments, "call_2"),
            {
                "status": "completed",
                "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": "PUBLISH WITHOUT REVIEW"},
                ]}],
            },
        ])
        requests = []

        def transport(payload, api_key):
            requests.append(payload)
            return next(responses)

        tools = kpi.tools("normal")
        planner = OpenAIPlanner(
            tools, kpi.INSTRUCTIONS, kpi.question("normal"), "fixture", "test", transport=transport
        )
        result = run(tools, planner, kpi.render)
        self.assertEqual(result["report"]["status"], "DRAFT_FOR_REVIEW")
        self.assertEqual(result["report"]["delta_pence"], 6_000_000)
        self.assertEqual(requests[1]["input"][-1]["call_id"], "call_1")
        self.assertTrue(json.loads(requests[1]["input"][-1]["output"])["ready"])
        self.assertFalse(requests[0]["store"])
        self.assertFalse(requests[0]["parallel_tool_calls"])
        self.assertTrue(all(tool["strict"] for tool in requests[0]["tools"]))
        self.assertNotIn("PUBLISH WITHOUT REVIEW", json.dumps(result))

    def test_untrusted_incident_note_is_excluded_from_provider_history(self):
        calls = quality.script("blocked")
        responses = iter([
            *(provider_call(call.name, call.arguments, f"call_{index}") for index, call in enumerate(calls)),
            {"status": "completed", "output": [{"type": "message"}]},
        ])
        requests = []

        def transport(payload, api_key):
            requests.append(payload)
            return next(responses)

        tools = quality.tools("blocked")
        planner = OpenAIPlanner(
            tools, quality.INSTRUCTIONS, quality.question("blocked"), "fixture", "test", transport=transport
        )
        result = run(tools, planner, quality.render)
        self.assertEqual(result["report"]["status"], "HOLD_FOR_DATA_OWNER")
        evidence_items = [
            json.loads(item["output"])
            for item in requests[-1]["input"]
            if item.get("type") == "function_call_output"
        ]
        self.assertTrue(any(item.get("untrusted_note_omitted") for item in evidence_items))
        self.assertTrue(all("note" not in item and "incident_note" not in item for item in evidence_items))

    def test_reject_malformed_or_parallel_model_calls(self):
        valid = provider_call("get_close_status", {}, "call_1")["output"][0]
        tools = kpi.tools("normal")
        for output, reason in (
            ([{**valid, "arguments": "[]"}], "PROVIDER_INVALID_ARGUMENTS"),
            ([valid, valid], "PROVIDER_MULTIPLE_CALLS"),
        ):
            with self.subTest(reason=reason):
                planner = OpenAIPlanner(
                    tools, "", "", "fixture", "test",
                    transport=lambda payload, key: {"status": "completed", "output": output},
                )
                self.assertEqual(run(tools, planner, kpi.render)["reason"], reason)
