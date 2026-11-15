# AI governance, strategy and implementation in analytics

I use this portfolio to show how I take an AI idea from selection and risk assessment to a working prototype. I built an SLA breach-risk model and two analytics agents around decisions a service desk, commercial analyst, or data operations team makes. The examples use synthetic data and leave operational decisions with the people who own them.

| Start here | What it covers |
| --- | --- |
| [AI strategy](docs/strategy.md) | Compare predictive triage, data-quality monitoring and generative KPI commentary. Set a baseline, review budget and criteria to move beyond a pilot. |
| [AI governance](docs/governance.md) and [sample risk register](docs/risk-register.md) | Assign accountability for data, model changes, human review, incident response and the decision to pause or release. |
| [Analytics implementation](docs/implementation.md) | Design the intake features, time-based evaluation and BI reporting. Trace the score through review, outcome and monitoring. |
| [Runnable Python demo](demo/README.md) | Train and evaluate a scikit-learn model, compare it with a priority rule, and inspect recommendations and manual fallback. |
| [AI agents and use cases](docs/ai-agent-use-cases.md) | Run a KPI variance investigation and a data quality triage. Inspect the tools, evidence and human review points. |

## Run the AI agents

I built two tool-using prototypes. One checks that reporting periods are closed before interpreting a variance. The other checks feed quality before recommending a human review. Both use a bounded set of read-only tools and generate reports from the evidence those tools return.

```bash
python -m agents kpi
python -m agents quality --scenario blocked
python -m unittest discover -s agents -t . -v
```

These commands run locally with Python 3.10 or newer and no additional packages. The default replays scripted tool calls. The [agent case studies](docs/ai-agent-use-cases.md) show the normal and blocked runs, the [optional model-backed setup](docs/ai-agent-use-cases.md#run-the-examples), and the controls I would test before a pilot.

## Run the SLA prediction prototype

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

## Related portfolio work

My [project delivery case study](https://github.com/teruece/Governance_Framework_Documentation_Toolkit/tree/main/project-delivery) shows how I track scope, risk, acceptance evidence and handover across a BI rollout.
