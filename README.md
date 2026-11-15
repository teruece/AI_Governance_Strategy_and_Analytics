# AI governance, strategy and implementation in analytics

A portfolio case study in taking an AI idea from selection and risk assessment to a working prototype. The example uses synthetic service-desk tickets to estimate SLA breach risk at intake. A queue analyst can use the score to choose which tickets to review. Priority changes stay with the analyst.

| Start here | What it covers |
| --- | --- |
| [AI strategy](docs/strategy.md) | Compare predictive triage, data-quality monitoring and generative KPI commentary. Set a baseline, review budget and criteria to move beyond a pilot. |
| [AI governance](docs/governance.md) and [sample risk register](docs/risk-register.md) | Assign accountability for data, model changes, human review, incident response and the decision to pause or release. |
| [Analytics implementation](docs/implementation.md) | Design the intake features, time-based evaluation and BI reporting. Trace the score through review, outcome and monitoring. |
| [Runnable Python demo](demo/README.md) | Train and evaluate a scikit-learn model, compare it with a priority rule, and inspect recommendations and manual fallback. |

## Run the prototype

From the repository root, install the pinned dependencies into a virtual environment. See the [demo guide](demo/README.md) for setup, commands and output.

```bash
python -m pip install -r demo/requirements.txt
python -m demo.sla_risk
```

The prototype generates all its inputs locally. It fits preprocessing and the model on the oldest period and evaluates on later periods after allowing time for SLA outcomes to mature. It shows the effect of a fixed review threshold and routes unsupported inputs to manual triage.

## What the synthetic evaluation shows

| Policy | Breach recall | Precision of review flags | Tickets flagged for review |
| --- | ---: | ---: | ---: |
| Model at the illustrative 0.40 threshold | 77.0% | 65.1% | 56.7% |
| High-priority-only rule | 30.9% | 70.3% | 21.0% |

The model flags more potential breaches and creates substantially more review work. The policies use different review volumes, so this comparison leaves open which policy performs better at the same review capacity. The strategy calls for an equal-capacity comparison on real, mature outcomes before live use. The metrics above are reproducible synthetic results. The production controls and rollout are reference designs.

The [SQL support SLA case](https://github.com/teruece/SQL_Codes_and_Projects/tree/main/use-cases/support-sla-ageing) demonstrates the point-in-time reporting logic that would sit alongside this predictive workflow.
