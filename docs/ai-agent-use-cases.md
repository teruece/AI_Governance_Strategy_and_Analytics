# AI agents for analytics and data operations

I built two AI-assisted portfolio prototypes around tasks an analyst can recognise. One investigates a change in a commercial KPI. The other triages a data quality incident. I used synthetic fixtures so the decisions, calculations and failure cases are reproducible.

## Commercial KPI variance agent

A commercial analyst receives a request to explain a change between two reporting periods. I start with the reporting close and reconciliation status. A variance can be arithmetically correct and still be misleading if one period is incomplete. Once the evidence is available, the agent can request the movement and its contributing drivers. Application code calculates the numbers and assembles the report from the tool results.

I would use the report to prepare a review with the commercial data owner. The review checks the comparison scope, the reconciliation to the total and any variance that needs investigating. The drivers describe how the total moved. Explaining the business cause still calls for context from the analyst.

## Data quality incident triage agent

A feed alert can reflect a late delivery, a material change in volume or a duplicate load. I designed this agent to inspect structured telemetry against the configured checks and produce evidence for the person who owns the next decision. The recommendation points to a manual review when a check fails. The data owner decides whether to investigate the source, rerun a job or hold a dependent report.

The blocked fixture includes an incident note with text that asks the agent to bypass a control. I keep the free-text note out of the planner input and use the freshness, volume and duplicate checks to decide the recommendation. In a live implementation I would also test manipulated telemetry and provenance, since excluding note text addresses only one source of misleading input.

## How I bounded the agent

The planner selects tools and proposes arguments. The runtime applies the rules before the tool executes, and the application builds the final report from structured evidence. I kept the calculations and safety checks in code so a reviewer can reproduce the decision with the same inputs.

| Design choice | What a reviewer can inspect |
| --- | --- |
| Read-only tools for each case | The tool list exposes only the synthetic evidence needed for that workflow. Human reviewers own publication, remediation and escalation. |
| Typed, allowlisted calls | The runtime checks tool names and arguments before execution. The tool code checks the requested scope and its business rules. |
| Finite execution budget | The runtime allows up to four planner turns, including the final response, and one accepted call per tool. It records accepted calls and provides a stop reason when a request fails a guard. |
| Evidence-based reports | Application code checks that the available results support the requested scope and uses them for the final status, figures and recommended review. |
| Scripted and model-backed planners | The offline path runs a known sequence for repeatable checks. The optional OpenAI path lets a model choose among the same tools. |

See the [OpenAI function calling guide](https://developers.openai.com/api/docs/guides/function-calling) for the model-to-tool interface and the [OWASP agent security guidance](https://owasp.github.io/DevSecOpsGuideline/2-Process/2-2-Develop/2-2-5-AI-Agent-and-MCP-Security/) for controls to consider in a live deployment.

## Run the examples

From the repository root, run the default scripted backend with Python 3.10 or newer. The commands use the standard library and the included synthetic fixtures.

```bash
python -m agents kpi
python -m agents kpi --scenario blocked
python -m agents quality
python -m agents quality --scenario blocked
python -m unittest discover -s agents -t . -v
```

| Scenario | Expected behaviour |
| --- | --- |
| KPI default | `DRAFT_FOR_REVIEW`. GB net sales rose £60,000 (+3.00%) from September to October 2026. Grocery contributed +£60,000, ecommerce +£30,000, and convenience −£30,000. |
| KPI blocked | `WITHHELD`. November is still open, so the tool returns the close evidence without sales figures. |
| Data quality default | `READY_FOR_HUMAN_REVIEW`. The feed is 15 minutes old and contains 9,950 rows with two duplicates. All three checks pass. |
| Data quality blocked | `HOLD_FOR_DATA_OWNER`. The feed is 125 minutes old, with 7,000 rows and 84 duplicates. Freshness, volume and duplicate checks all fail. The report records that the note was omitted. |

To exercise the model-backed planner, set `OPENAI_API_KEY` in your environment and replace `YOUR_MODEL_ID` with a supported model in your account. This sends the synthetic case and tool results to the Responses API and can incur usage charges.

```bash
python -m agents kpi --backend openai --model YOUR_MODEL_ID
```

The scripted runs exercise tool controls and case logic. Automated tests also exercise the model adapter with simulated API responses. A live API run is a separate evaluation step. I would measure model tool selection, completeness and behaviour under unexpected inputs before relying on that path.

## What I would measure before rollout

I would start with historical cases that an analyst has already resolved, replay only the information available at the time and compare results with the existing KPI review or alert runbook. The proposed scorecard measures valid tool calls, agreement with verified figures and expected triage, the rate of safe stops on incomplete evidence, and analyst review time. I would include mismatched periods, duplicate records, missing telemetry, unavailable tools and attempts to steer the planner outside its scope.

For a live pilot, I would give the agent a separate read-only identity limited to approved views. Each report would carry evidence identifiers, source freshness, tool and model versions and a run ID. A restricted audit record would capture denials, stop reasons and the human review outcome. The commercial owner would approve KPI commentary, and the data operations owner would approve remediation through the existing process. If a control failed, I would switch the team back to its existing review workflow while the owner investigates.

The [AI strategy](strategy.md) sets out how I would prioritise a pilot. The [governance operating model](governance.md) and [risk register](risk-register.md) cover ownership, monitoring and release decisions.
