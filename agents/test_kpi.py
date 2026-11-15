import unittest
from copy import deepcopy
from unittest.mock import patch

from agents import kpi


class KpiCaseTests(unittest.TestCase):
    def setUp(self):
        self.tools = {tool.name: tool for tool in kpi.tools("normal")}
        self.arguments = {"current_period": "2026-10", "comparison_period": "2026-09"}

    def run_tools(self):
        return {name: tool.execute(self.arguments) for name, tool in self.tools.items()}

    def test_closed_pair_reconciles_and_channel_deltas_add_up(self):
        result = kpi.render(self.run_tools())
        self.assertEqual(result["status"], "DRAFT_FOR_REVIEW")
        self.assertEqual(result["current_pence"], 206_000_000)
        self.assertEqual(result["comparison_pence"], 200_000_000)
        self.assertEqual(result["delta_pence"], 6_000_000)
        self.assertEqual(result["delta_percent"], "3.00")
        contributions = {row["channel"]: row["delta_pence"] for row in result["channel_contributions"]}
        self.assertEqual(contributions, {"convenience": -3_000_000, "ecommerce": 3_000_000, "grocery": 6_000_000})
        self.assertEqual(sum(contributions.values()), result["delta_pence"])
        self.assertEqual(len(result["evidence_ids"]), 2)

    def test_open_period_returns_no_sales_even_if_tool_is_called_directly(self):
        close, sales = kpi.tools("blocked")
        parameters = {"current_period": "2026-11", "comparison_period": "2026-10"}
        self.assertEqual([call.name for call in kpi.script("blocked")], [close.name])
        result = kpi.render({close.name: close.execute(parameters), sales.name: sales.execute(parameters)})
        self.assertEqual(result["status"], "WITHHELD")
        self.assertEqual(result["periods"][0]["close_status"], "OPEN")
        self.assertNotIn("current_pence", sales.execute(parameters))
        self.assertNotIn("channel_contributions", result)

    def test_tool_scope_rejects_other_periods_and_filters(self):
        for arguments in (
            {"current_period": "2026-11", "comparison_period": "2026-10"},
            {**self.arguments, "market": "DE"},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.tools["get_sales_variance"].execute(arguments)

    def test_close_evidence_must_match_the_requested_variance(self):
        evidence = self.run_tools()
        variance_only = {"get_sales_variance": evidence["get_sales_variance"]}
        self.assertEqual(kpi.render(variance_only)["status"], "INSUFFICIENT_EVIDENCE")
        mismatched = deepcopy(evidence)
        mismatched["get_sales_variance"]["scope"]["market"] = "DE"
        self.assertEqual(kpi.render(mismatched)["status"], "INSUFFICIENT_EVIDENCE")

    def test_reconciliation_error_blocks_variance_and_output(self):
        with patch.dict(kpi._CLOSE_LEDGER_PENCE, {"2026-10": 206_000_001}):
            evidence = self.run_tools()
        result = kpi.render(evidence)
        self.assertEqual(result["status"], "WITHHELD")
        self.assertEqual(result["periods"][0]["reconciliation_difference_pence"], -1)
        self.assertNotIn("channels", evidence["get_sales_variance"])

    def test_channel_total_mismatch_withholds_draft(self):
        evidence = self.run_tools()
        evidence["get_sales_variance"]["channels"][0]["delta_pence"] += 1
        self.assertEqual(kpi.render(evidence)["status"], "WITHHELD")

    def test_channels_present_in_only_one_period_keep_the_headline_additive(self):
        snapshots = {
            "2026-09": {"grocery": 120_000_000, "wholesale": 80_000_000},
            "2026-10": {"grocery": 126_000_000, "ecommerce": 80_000_000},
        }
        with patch.dict(kpi._CHANNEL_SALES_PENCE, snapshots):
            result = kpi.render(self.run_tools())
        contributions = {
            row["channel"]: row["delta_pence"] for row in result["channel_contributions"]
        }
        self.assertEqual(contributions["wholesale"], -80_000_000)
        self.assertEqual(contributions["ecommerce"], 80_000_000)
        self.assertEqual(sum(contributions.values()), result["delta_pence"])
