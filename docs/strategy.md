# AI strategy for service desk analytics

In this scenario, a service desk uses [point-in-time SQL reporting](https://github.com/teruece/SQL_Codes_and_Projects/tree/main/use-cases/support-sla-ageing) to see overdue tickets and approaching deadlines. That report answers which tickets need attention now. This portfolio case evaluates a separate decision at ticket creation. An analyst can use a breach-risk score to decide which newly opened tickets to review first, before the SLA clock runs down. The existing SLA rules remain the source of truth for escalation and priority.

The implementation uses synthetic tickets and outcomes, plus a fixed example alert threshold, to demonstrate the design. The pilot thresholds, staffing figures and costs below are illustrative inputs for a real approval decision.

## Prioritise by the decision and the evidence

Rate each candidate from 1 to 5 on operational value, readiness of the required data, ability to measure results, and ease of controlling adverse effects. A 5 indicates a clear action, available evidence or straightforward controls for that criterion. Apply weights of 35%, 25%, 25% and 15% respectively. Score the proposals only after confirming a decision owner, a permitted data source and a workable human review process.

| Use case | Value | Data | Measurement | Control | Score | Evidence behind the rating |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Predict SLA breach risk at ticket creation | 5 | 4 | 5 | 4 | **4.60** | Analysts can review flagged tickets. An existing SQL definition supplies an outcome. Historical feature availability and queue coverage still need proof. |
| Flag unusual source-feed volumes | 3 | 4 | 4 | 5 | **3.80** | Batch history and incident records support a backtest. Fixed freshness and completeness checks provide a useful baseline. |
| Draft weekly KPI narratives with generative AI | 3 | 3 | 3 | 2 | **2.85** | Candidate time savings depend on review effort, metric grounding, citation checks and a controlled publication flow. |

Pilot predictive triage first. Compare it with both analyst practice and a simple rules-based ranking under the same review budget. Start source-feed monitoring with deterministic checks, then test anomaly scoring if those checks leave meaningful gaps. A KPI narrative pilot would require approved source access, evidence for each reported claim and editorial sign-off before distribution.

## Define evidence before releasing scores

Record the opportunity to intervene, the action the analyst took and the subsequent outcome separately. Use the same SLA definition in the SQL baseline and the evaluation. Exclude outcomes that are still unobservable at the evaluation cutoff. For each evaluation window, report the number of eligible tickets, flagged tickets and observed breaches by supported queue.

| Gate | Evidence and decision |
| --- | --- |
| Offline feasibility | The data owner demonstrates that every feature existed when the ticket was opened. The analytics lead uses chronological training, validation and held-out windows. Set the alert threshold on validation data. Compare held-out precision and recall with the rules baseline at the same practical review capacity. An illustrative gate requires at least 35% precision, at least 50% recall and precision equal to or above the baseline at comparable alert volume. Investigate queue-level error differences and insufficient history before requesting shadow operation. |
| Shadow pilot | Run the scored feed for four weeks with scores hidden from the operational queue. Check delivered volumes, missing or unsupported inputs, eligible label coverage, and queue-level false negatives once outcomes mature. Plan for up to 60 additional reviews per week. A queue with fewer than 30 observed breaches stays in shadow until enough outcomes are available to review. Confirm analyst access, escalation ownership and fallback. |
| Assisted pilot and scale | Launch to a limited set of approved queues. Analysts review recommendations and record their decisions. Where the operation can support it, use a concurrent comparison with the current process and track SLA breaches per 100 eligible tickets, reviews per week, and analyst minutes per review. Scale only if the accountable owner sees a credible operational benefit, acceptable review effort, usable evidence across queues and sign-off on material controls. Record the decision and conditions. |
| Pause or stop | Pause scores on a broken feature feed, lost audit evidence, unexpected queue coverage gaps, or observed harm. A lead reviews sustained volume above the weekly capacity, degraded precision once outcomes mature, or a material rise in missed breaches for a queue. Return analysts to the existing SQL SLA workflow while owners investigate and verify any fix. |

The offline model can tell us how often the system would flag a future breach in the synthetic data. A real pilot needs separate evidence to estimate whether analyst intervention changes the outcome. Once analysts intervene, their actions can change the observed breach rate, so keep comparison-group data where available and account for recorded interventions when interpreting the results.

## Build, buy and operate

Use the local model for a transparent feasibility test. It gives the analytics team control over feature timing, evaluation and the alert threshold. Reassess an existing service-desk vendor's scoring features before investing in production integration. Compare exportable scores and explanations, incident support, fit with the SLA definition, retraining responsibilities, queue-level evidence and total operating cost. Choose the simplest option that meets the review capacity and control requirements.

The **service desk owner** is accountable for the review process, capacity and go or stop decision. The **analytics lead** owns the feature contract, evaluation and monitoring. The **data owner** validates the point-in-time fields and SLA outcome. The **platform owner** handles access, reliable score delivery and fallback. Analysts own review decisions and can report unhelpful or incorrect scores to the service desk owner.

An illustrative weekly estimate uses 60 reviews at three minutes each and £30 per analyst hour, plus £35 in recurring platform and support costs. That is £125 per week. At an assumed £12 of avoidable handling cost per prevented breach, the pilot would need at least 11 prevented breaches per week to cover recurring cost. Validate the handling-cost assumption and any measured prevention separately, and add one-off build and training costs before making a scale decision.

See the [governance operating model](governance.md) for ownership and controls, and the [implementation](implementation.md) for the demo's evaluation design and run instructions.
