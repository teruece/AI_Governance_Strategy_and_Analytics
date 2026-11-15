# Run the SLA breach risk demo

The demo uses synthetic service-desk tickets to compare a logistic regression model with a high-priority review rule. It prints a JSON evaluation and three example recommendations. Use Python 3.11 or 3.12 and run these commands from the repository root.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r demo/requirements.txt
python -m demo.sla_risk
python -m unittest demo.test_sla_risk -v
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1` before installing dependencies. Training, evaluation, and sample scoring run locally after installation.

| Expected held-out result | Model at 0.40 | High-priority rule |
| --- | ---: | ---: |
| Review suggestions | 272 of 480 | 101 of 480 |
| Share proposed for review | 56.67% | 21.04% |
| Recall | 76.96% | 30.87% |
| Precision | 65.07% | 70.30% |
| False-positive rate | 38.00% | 12.00% |

The model flags more breaches and consumes more review capacity. The threshold is fixed for the demonstration. Synthetic results describe this fixture. Use a properly governed pilot to measure whether a model helps with actual tickets.

The JSON includes model results by queue, plus one example each for a review suggestion, standard triage, and manual triage with an unsupported queue. Queue results diagnose workload distribution across operational groups. They provide no evidence about protected groups. Probabilities are rounded for display after applying the decision threshold. The printed actions are options for a human analyst. They leave routing and priority decisions with the triage team.
