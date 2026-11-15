import json
import unittest

from . import quality


def collect(scenario):
    tools = {tool.name: tool for tool in quality.tools(scenario)}
    return {
        call.name: tools[call.name].execute(call.arguments)
        for call in quality.script(scenario)
    }


class DataQualityTests(unittest.TestCase):
    def test_normal_batch_is_ready_for_human_review(self):
        result = quality.render(collect("normal"))
        self.assertEqual(result["status"], "READY_FOR_HUMAN_REVIEW")
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(result["checks"]["freshness"]["age_minutes"], 15)
        self.assertFalse(result["untrusted_note_omitted"])

    def test_blocked_batch_routes_to_data_owner_and_omits_note(self):
        evidence = collect("blocked")
        result = quality.render(evidence)
        self.assertEqual(result["status"], "HOLD_FOR_DATA_OWNER")
        self.assertEqual(result["checks"]["freshness"]["age_minutes"], 125)
        self.assertEqual(
            result["failed_checks"],
            ["STALE_FEED", "ROW_COUNT_OUT_OF_RANGE", "DUPLICATE_RATE_EXCEEDED"],
        )
        self.assertTrue(result["untrusted_note_omitted"])
        raw_note = quality._BATCHES["blocked"]["operator_note"]
        self.assertNotIn(raw_note, json.dumps(evidence))
        self.assertNotIn(raw_note, quality.question("blocked"))
        self.assertNotIn(raw_note, json.dumps(result))
        self.assertIn("data owner", result["suggested_next_step"])

    def test_tool_cannot_read_another_batch_or_accept_extra_arguments(self):
        for tool, call in zip(quality.tools("blocked"), quality.script("normal")):
            with self.assertRaises(ValueError):
                tool.execute(call.arguments)
        for tool, call in zip(quality.tools("normal"), quality.script("normal")):
            with self.assertRaises(ValueError):
                tool.execute({**call.arguments, "approval_override": True})

    def test_incomplete_or_mismatched_evidence_stays_on_hold(self):
        normal = collect("normal")
        blocked = collect("blocked")
        for evidence in (
            {quality.GET_TELEMETRY: normal[quality.GET_TELEMETRY]},
            {**normal, quality.GET_POLICY: blocked[quality.GET_POLICY]},
        ):
            with self.subTest(evidence=evidence):
                self.assertEqual(quality.render(evidence)["status"], "INSUFFICIENT_EVIDENCE")

    def test_inclusive_policy_boundaries(self):
        evidence = collect("normal")
        evidence[quality.GET_TELEMETRY].update(
            row_count=9_000,
            duplicate_rows=45,
            received_at="2026-04-18T07:00:00+00:00",
        )
        self.assertEqual(quality.render(evidence)["failed_checks"], [])
        evidence[quality.GET_TELEMETRY]["duplicate_rows"] = 46
        self.assertEqual(quality.render(evidence)["failed_checks"], ["DUPLICATE_RATE_EXCEEDED"])

    def test_future_arrival_does_not_count_as_fresh(self):
        evidence = collect("normal")
        evidence[quality.GET_TELEMETRY]["received_at"] = "2026-04-18T08:01:00+00:00"
        self.assertEqual(quality.render(evidence)["status"], "INSUFFICIENT_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
