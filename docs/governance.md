# AI governance operating model

The case study scores the risk of a service-desk ticket breaching its resolution SLA at the moment it enters the queue. A supervisor uses the signal to decide which tickets merit a closer look. The ticketing system supplies the authoritative SLA clock and priority. An analyst reviews the ticket and applies the existing escalation policy. People affected by the workflow include requesters whose cases may receive different amounts of attention and analysts who need to understand and challenge the recommendation.

This operating model uses the four core functions in the NIST AI Risk Management Framework. It pairs a completed synthetic [use-case and risk register](risk-register.md) with decisions an organisation would have to make before a live pilot. [NIST AI Risk Management Framework 1.0](https://doi.org/10.6028/NIST.AI.100-1)

| Function | How it applies to SLA triage | Review evidence |
| --- | --- | --- |
| Govern | Assign a business owner, technical owner and independent reviewer. Keep intended use, model version and risk decisions in a register. | Register, named sign-offs, change history and incident contact |
| Map | Identify where the score enters the workflow, who relies on it and what happens when it is wrong. Confirm that each feature exists at ticket creation. | Data contract, feature availability and workflow diagram |
| Measure | Compare the model with the analyst's baseline. Check alert volume, missed breaches and results by eligible queue. | Chronological test report, queue metrics, sample size and review capacity |
| Manage | Start in shadow mode. Release only after evidence review. Pause the signal and use manual triage if a trigger is met. | Release decision, monitoring record and rollback rehearsal |

## Ownership and oversight

| Role | Decision or responsibility |
| --- | --- |
| Service operations owner | Owns intended use, reviewer capacity, pilot criteria and the decision to release, suspend or retire the service. |
| Analytics product owner | Maintains the use-case register and evidence pack, coordinates reviews and records decisions and due dates. |
| Model owner | Versions the data contract, code and threshold. Produces an evaluation report and explains changes, failures and limitations. |
| Independent reviewer | Challenges the point-in-time feature audit, evaluates the cost of errors and checks that pilot evidence supports the release decision. |
| Data steward | Approves intake data, access, provenance, retention and deletion under the organisation's data policy. |
| Shift supervisor | Owns the review queue and escalation decisions. Captures feedback and can request a pause when the signal degrades. |
| Platform operator | Owns deployment, feed health, audit access and the mechanism for reverting to manual triage. |

The reviewer sees the score, the model and threshold version, and a short explanation of the feature inputs at scoring time. The interface distinguishes a low score from an unavailable or unsupported score. The analyst can dismiss or escalate a recommendation and capture a reason. A requester can raise a missed or inappropriate escalation through the existing support route. The shift supervisor reviews the underlying ticket, corrects the operational action when appropriate and records the feedback for periodic review. In a pilot, the score panel and action trail would be accessible only to the authorised support team.

## Evidence and decision gates

The [implementation](implementation.md) describes the executable sandbox and records how it was tested. The public demo fits on an earlier period and checks a fixed 0.40 review threshold against a high-priority rule. Its report includes queue-level diagnostics on the synthetic test period, and its scoring policy returns unsupported inputs to manual triage. The following gates describe a proposed live pilot and require separate evidence.

| Gate | Evidence to bring to review | Decision |
| --- | --- | --- |
| Intake | Intended decision and population, baseline rule, impact if wrong, approved data fields, source owners and per-field availability time | Service operations owner and data steward approve shadow scope. |
| Offline review | Chronological backtest, comparable baseline, alerts per day, queue-level missed-breach rates and a sample of errors reviewed by analysts | Independent reviewer records evidence, limitations and required actions. |
| Shadow run | Score alongside existing triage. Observe volume, latency, unavailable scores and mature SLA outcomes for approved queues. | Service operations owner decides whether reviewers have capacity and the evidence supports a limited pilot. |
| Limited release | Versioned model, threshold and data contract, support handover, monitoring owners and a successful pause/revert exercise | Service operations owner records the decision, scope, expiry date and review schedule. |
| Material change | New queue, feature, threshold, label policy, model version or use of text/external services. Rerun affected validation and confirm approval. | Analytics product owner routes the change back through the relevant gates. |

## Monitoring and rollback

Set production thresholds before evaluating the pilot. Start with the following illustrative triggers and adjust them to local staffing and SLA needs.

| Signal | Example rule | Owner and response |
| --- | --- | --- |
| Data contract or model version | Required field removed, feature timestamps after ticket creation, or unexpected version | Platform operator pauses scoring immediately. Model owner traces the affected time window and validates a corrected release. |
| Unsupported or unavailable scores | More than 5% of incoming records in an approved queue during a shift, with at least 30 tickets | Shift supervisor redirects all affected tickets to manual triage. Model owner investigates coverage and input changes. |
| Review demand | Recommendations exceed 20 per staffed shift for two consecutive shifts | Operations owner checks workload and handoff quality. Threshold changes go through validation and approval. |
| Missed breaches by queue | Missed-breach rate is more than 15 percentage points above the aggregate for two weekly periods, with at least 30 confirmed breaches in each queue period | Independent reviewer investigates representation, policy differences and model performance before expanding the affected queue. |
| Leakage or access incident | Ticket data is exposed to an unauthorised audience, or retrospective data was used as a scoring input | Platform operator restricts access and pauses the signal. The service owner opens the incident record and brings in the relevant security or data governance team. |

Track alerts, overrides, input errors and use of the fallback each shift. Review precision and missed breaches on mature outcomes, after tickets have closed or exceeded their deadline by the agreed observation cutoff. Segment by queue and show counts with rates. Insufficient volume calls for investigation over a longer window and a review of sample cases. Operational queue comparisons can surface workflow disparities and research questions. A separate review would be needed to assess fairness for people or populations in a live service.

To roll back, the platform operator turns off new scores and removes the signal from the triage interface. The shift supervisor routes work through manual triage and confirms that tickets continue to appear in the appropriate queues. Reconcile the affected date range and re-review tickets whose decisions may have been influenced. Record the reason, impact, model version, rollback time and owner. Restart only after the affected cases have been reconciled, the fix and current evaluation have passed review, and the service owner has approved restart.

## Data and audit controls

Use a whitelist of ticket-creation fields for scoring. Store a feature timestamp and source version alongside each production score so a reviewer can reconstruct what was known at the time. Keep outcome and closure fields in the evaluation view. Capture the ticket key, score time, model and threshold version, recommendation, analyst decision and reason in a restricted audit table. Assign retention and deletion windows with the data steward before ingesting real records. Audit access and preserve a minimal incident record under the organisation's process.

The current case uses structured data and a local model. Adding ticket text, generative output or a third-party model would change the data flow and impact profile. At intake, map what gets transmitted or retained, assess vendor access and retention, test for leakage and unreliable output, and define a manual fallback before any expanded pilot. See the [strategy](strategy.md) for scope and sequencing, and the [repository overview](../README.md) for the demo.
