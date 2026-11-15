"""Train and evaluate a synthetic support-ticket review model."""

import argparse
import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import exp

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

QUEUES = ("access", "billing", "platform")
PRIORITIES = ("standard", "high")
SLA_HOURS = (4, 8, 12)
REVIEW_THRESHOLD = 0.40
SEED = 17

START = datetime(2025, 1, 1, tzinfo=UTC)
TRAIN_END = datetime(2025, 5, 1, tzinfo=UTC)
VALIDATION_END = datetime(2025, 7, 1, tzinfo=UTC)
TEST_END = datetime(2025, 9, 1, tzinfo=UTC)
MATURITY_GAP = timedelta(days=2)


@dataclass(frozen=True)
class Intake:
    created_at: datetime
    queue: str
    priority: str
    backlog_at_intake: int
    sla_hours: int

    @property
    def off_hours(self) -> bool:
        hour = self.created_at.astimezone(UTC).hour
        return hour < 8 or hour >= 18


@dataclass(frozen=True)
class Ticket:
    intake: Intake
    resolved_at: datetime

    @property
    def breached(self) -> bool:
        deadline = self.intake.created_at + timedelta(hours=self.intake.sla_hours)
        return self.resolved_at > deadline


def synthetic_tickets() -> list[Ticket]:
    """Generate intake snapshots and resolution times using a fixed seed."""
    generator = random.Random(SEED)
    tickets = []
    for day in range((TEST_END - START).days):
        for hour in range(0, 24, 3):
            created = START + timedelta(days=day, hours=hour)
            queue = generator.choice(QUEUES)
            priority = generator.choices(PRIORITIES, weights=(8, 2))[0]
            backlog = generator.randrange(5, 101)
            sla_hours = generator.choice(SLA_HOURS)
            intake = Intake(created, queue, priority, backlog, sla_hours)

            # Synthetic outcome mechanism. The model does not receive this formula.
            log_odds = (
                -3.1
                + 0.035 * backlog
                + 0.9 * (priority == "high")
                + 0.85 * intake.off_hours
                + 0.6 * (queue == "platform")
                + 0.7 * (sla_hours == 4)
            )
            chance = 1 / (1 + exp(-log_odds))
            deadline_minutes = sla_hours * 60
            if generator.random() < chance:
                duration = deadline_minutes + generator.randint(1, 360)
            else:
                duration = generator.randint(1, deadline_minutes)
            tickets.append(Ticket(intake, created + timedelta(minutes=duration)))
    return tickets


def split_tickets(tickets: list[Ticket]) -> dict[str, list[Ticket]]:
    """Partition by intake time and leave near-boundary tickets out."""
    periods = {
        "train": (START, TRAIN_END),
        "validation": (TRAIN_END, VALIDATION_END),
        "test": (VALIDATION_END, TEST_END),
    }
    splits = {}
    for name, (start, cutoff) in periods.items():
        rows = [
            ticket
            for ticket in tickets
            if start <= ticket.intake.created_at < cutoff - MATURITY_GAP
        ]
        if any(ticket.resolved_at > cutoff for ticket in rows):
            raise ValueError(f"{name} has an outcome unavailable at its cutoff")
        splits[name] = rows
    return splits


def features(intake: Intake) -> dict[str, str | int]:
    """Project the intake allowlist. Outcomes never enter the model."""
    return {
        "queue": intake.queue,
        "priority": intake.priority,
        "backlog_at_intake": intake.backlog_at_intake,
        "sla_hours": intake.sla_hours,
        "off_hours": int(intake.off_hours),
    }


def fit_model(train: list[Ticket]):
    model = make_pipeline(
        DictVectorizer(),
        StandardScaler(with_mean=False),
        LogisticRegression(random_state=SEED),
    )
    return model.fit(
        [features(ticket.intake) for ticket in train],
        [ticket.breached for ticket in train],
    )


def scope_exception(intake: Intake) -> str | None:
    if intake.queue not in QUEUES:
        return "UNSUPPORTED_QUEUE"
    if intake.priority not in PRIORITIES:
        return "UNSUPPORTED_PRIORITY"
    if type(intake.backlog_at_intake) is not int or not 5 <= intake.backlog_at_intake <= 100:
        return "UNSUPPORTED_BACKLOG"
    if type(intake.sla_hours) is not int or intake.sla_hours not in SLA_HOURS:
        return "UNSUPPORTED_SLA"
    if not isinstance(intake.created_at, datetime) or intake.created_at.utcoffset() is None:
        return "MISSING_EXPLICIT_TIME_ZONE"
    return None


def triage_action(probability: float) -> str:
    return "REVIEW_SUGGESTED" if probability >= REVIEW_THRESHOLD else "STANDARD_TRIAGE"


def score_ticket(model, intake: Intake) -> dict:
    reason = scope_exception(intake)
    if reason:
        return {"action": "MANUAL_TRIAGE", "reason": reason, "breach_score": None}
    probability = float(model.predict_proba([features(intake)])[0, 1])
    return {
        "action": triage_action(probability),
        "reason": None,
        "breach_score": round(probability, 4),
    }


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def classification_metrics(labels: list[bool], review_flags: list[bool]) -> dict:
    true_positive = sum(label and flag for label, flag in zip(labels, review_flags, strict=True))
    breaches = sum(labels)
    reviews = sum(review_flags)
    return {
        "tickets": len(labels),
        "breaches": breaches,
        "review_suggestions": reviews,
        "review_share": ratio(reviews, len(labels)),
        "recall": ratio(true_positive, breaches),
        "precision": ratio(true_positive, reviews),
        "false_positive_rate": ratio(reviews - true_positive, len(labels) - breaches),
    }


def evaluate(model, tickets: list[Ticket], include_queue_diagnostics: bool = False) -> dict:
    labels = [ticket.breached for ticket in tickets]
    scores = model.predict_proba([features(ticket.intake) for ticket in tickets])[:, 1]
    model_flags = [triage_action(score) == "REVIEW_SUGGESTED" for score in scores]
    baseline_flags = [ticket.intake.priority == "high" for ticket in tickets]
    results = {
        "model": classification_metrics(labels, model_flags),
        "high_priority_baseline": classification_metrics(labels, baseline_flags),
        "average_precision": round(float(average_precision_score(labels, scores)), 4),
        "brier_score": round(float(brier_score_loss(labels, scores)), 4),
    }
    if include_queue_diagnostics:
        by_queue = {}
        for queue in QUEUES:
            indices = [index for index, ticket in enumerate(tickets) if ticket.intake.queue == queue]
            by_queue[queue] = classification_metrics(
                [labels[index] for index in indices],
                [model_flags[index] for index in indices],
            )
        results["model_by_queue"] = by_queue
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    splits = split_tickets(synthetic_tickets())
    model = fit_model(splits["train"])
    scoring_examples = {
        "higher_risk": Intake(TEST_END, "platform", "high", 95, 4),
        "lower_risk": Intake(TEST_END.replace(hour=10), "access", "standard", 12, 12),
        "unsupported_queue": Intake(TEST_END, "out_of_scope", "high", 95, 4),
    }
    results = {
        "fixture": "synthetic",
        "review_threshold": REVIEW_THRESHOLD,
        "training_rows": len(splits["train"]),
        "validation": evaluate(model, splits["validation"]),
        "test": evaluate(model, splits["test"], include_queue_diagnostics=True),
        "examples": {name: score_ticket(model, intake) for name, intake in scoring_examples.items()},
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
