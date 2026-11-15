import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from demo import sla_risk


class SlaRiskTests(unittest.TestCase):
    def setUp(self):
        self.intake = sla_risk.Intake(
            datetime(2025, 1, 1, 12, tzinfo=UTC), "billing", "standard", 35, 8
        )

    def test_resolution_at_deadline_is_met(self):
        deadline = self.intake.created_at + timedelta(hours=self.intake.sla_hours)
        self.assertFalse(sla_risk.Ticket(self.intake, deadline).breached)
        self.assertTrue(
            sla_risk.Ticket(self.intake, deadline + timedelta(seconds=1)).breached
        )

    def test_splits_are_chronological_and_leave_maturity_gaps(self):
        parts = sla_risk.split_tickets(sla_risk.synthetic_tickets())
        start = sla_risk.START
        for name, cutoff, count in (
            ("train", sla_risk.TRAIN_END, 944),
            ("validation", sla_risk.VALIDATION_END, 472),
            ("test", sla_risk.TEST_END, 480),
        ):
            rows = parts[name]
            self.assertEqual(len(rows), count)
            self.assertTrue(
                all(
                    start <= row.intake.created_at < cutoff - sla_risk.MATURITY_GAP
                    and row.resolved_at <= cutoff
                    for row in rows
                )
            )
            start = cutoff

    def test_split_fails_on_unavailable_outcome(self):
        future_resolution = sla_risk.TRAIN_END + timedelta(minutes=1)
        with self.assertRaisesRegex(ValueError, "outcome unavailable"):
            sla_risk.split_tickets([sla_risk.Ticket(self.intake, future_resolution)])

    def test_features_are_intake_only(self):
        self.assertEqual(
            sla_risk.features(self.intake),
            {
                "queue": "billing",
                "priority": "standard",
                "backlog_at_intake": 35,
                "sla_hours": 8,
                "off_hours": 0,
            },
        )

    def test_unsupported_intake_never_calls_model(self):
        for changes, reason in (
            ({"queue": "unknown"}, "UNSUPPORTED_QUEUE"),
            ({"priority": "urgent"}, "UNSUPPORTED_PRIORITY"),
            ({"backlog_at_intake": 3}, "UNSUPPORTED_BACKLOG"),
            ({"sla_hours": 7}, "UNSUPPORTED_SLA"),
            ({"created_at": self.intake.created_at.replace(tzinfo=None)}, "MISSING_EXPLICIT_TIME_ZONE"),
        ):
            with self.subTest(reason=reason):
                result = sla_risk.score_ticket(None, replace(self.intake, **changes))
                self.assertEqual(
                    result, {"action": "MANUAL_TRIAGE", "reason": reason, "breach_score": None}
                )

    def test_threshold_is_inclusive(self):
        self.assertEqual(sla_risk.triage_action(0.40), "REVIEW_SUGGESTED")
        self.assertEqual(sla_risk.triage_action(0.39999), "STANDARD_TRIAGE")

    def test_fixture_evaluation_reconciles_to_queue_totals(self):
        parts = sla_risk.split_tickets(sla_risk.synthetic_tickets())
        model = sla_risk.fit_model(parts["train"])
        results = sla_risk.evaluate(model, parts["test"], include_queue_diagnostics=True)
        self.assertEqual(results["model"]["tickets"], 480)
        self.assertEqual(results["model"]["breaches"], 230)
        self.assertEqual(results["model"]["review_suggestions"], 272)
        self.assertEqual(
            sum(queue["review_suggestions"] for queue in results["model_by_queue"].values()),
            results["model"]["review_suggestions"],
        )


if __name__ == "__main__":
    unittest.main()
