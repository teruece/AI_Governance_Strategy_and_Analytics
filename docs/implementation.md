# Implementing AI in analytics

The prototype estimates the risk of a service-desk ticket breaching its resolution SLA at the moment it enters the queue. A high score sends the ticket for a second look. The queue owner keeps responsibility for ticket priority, staffing and SLA exceptions.

The demo runs locally on synthetic data. The data contracts, reporting model and rollout below show how a team could take the prototype into a controlled pilot.

## From reporting to a score

Start with an agreed SLA definition. The [point-in-time SQL example](https://github.com/teruece/SQL_Codes_and_Projects/tree/main/use-cases/support-sla-ageing) shows how a service desk can report overdue work at a given cutoff. The prediction answers an earlier question using only what the queue knew at intake. An already overdue ticket still belongs in the normal escalation process.

| Item | Implementation decision |
| --- | --- |
| Unit of analysis | One first-intake snapshot per ticket. Replay should retain the original feature timestamp and model version so that a later report can reproduce the decision context. |
| Target | Breach of the ticket's resolution SLA. When deriving the label in production, wait until the original SLA deadline and source freshness are both known. A resolution at the deadline meets the SLA. |
| Features | Queue, intake priority, backlog at intake, SLA hours and whether the ticket arrived outside support hours. A backlog query must use the actual intake cutoff. |
| Data preparation | The local model uses historical time splits and fits preprocessing on training rows. In a pilot, freeze the feature view and document late data handling before scoring. |
| Reviewer action | Compare the review flag with the current queue state. Record whether the suggested review was useful and why any change was made. |
| Fallback | Route unsupported inputs to normal manual triage. If the feed is stale, scoring fails, or the queue is outside the approved scope, keep SLA reporting available and suppress new recommendations. |

Closure timestamps, final priority, escalations and comments added after intake can be useful for diagnosis. Including them in intake features would leak information unavailable at decision time. A pilot should keep the intake snapshot separate from later outcomes and join them only for evaluation.

## Evaluate before expanding access

1. Fit transformations and the estimator on the oldest labelled period. Keep later validation and test periods separate.
2. Agree a baseline with operations. The demo compares the model with an intake-priority rule. Compare recall, precision and review count together to see the operational cost of catching more breaches.
3. Record the review threshold before opening the test results. The demo uses an illustrative threshold. A production decision needs validation on representative history and agreement on daily review capacity.
4. Report per-queue counts with the rates. Suppress or annotate unstable estimates from small groups. Investigate whether a queue has unusual input missingness or delayed outcome capture before interpreting the gap.
5. In shadow mode, score live tickets and compare decisions with the established process. Give reviewers a way to flag misleading recommendations, and retain aggregated pilot evidence for the release decision.

A ticket reviewed early may be resolved before it breaches. That changes the observed outcome. To estimate operational benefit after the pilot starts, use a comparison design agreed with the service owner. Treat high recall on historical data as model evidence and compare actual review workload and SLA performance separately.

## Publish the evidence in BI

A governed analytics view can join the intake score, subsequent review disposition and matured SLA outcome. Keep their timestamps separate, and use a left join so unresolved or unreviewed cases stay visible as pending.

| Output | Grain | Example fields |
| --- | --- | --- |
| Score log | Ticket, intake timestamp and model version | Dataset timestamp, breach score, threshold, review flag, fallback reason |
| Review log | Ticket and review event | Reviewed at, disposition, standardised reason, authorised reviewer reference |
| SLA outcomes | Ticket and outcome version | SLA deadline, matured at, breach indicator, source freshness |
| Monitoring view | Week, queue and model version | Eligible tickets, scored tickets, review flags, fallback count, outcome sample size, precision and recall |

For coverage, divide scored tickets by eligible intake tickets. For workload, divide review flags by eligible intake tickets and include the count. Compute precision and recall only on rows with mature outcomes. Include the outcome window and the denominator on each report page so a late feed cannot look like a sudden drop in model quality. If reviewers see ticket-level details, apply the queue's existing access rules and test service roles before sharing the report.

## Operational rollout

- Run the demo and review the synthetic evidence. Record the evaluation version, feature contract and tests.
- Pilot in shadow mode for approved queues. Record which signals reach analysts, how often the feed fails, and whether a threshold leaves room for the existing review workload.
- Enable the flag for a limited set of reviewers after the service owner accepts the evidence and the platform owner tests the off switch. Leave existing SLA routing active.
- If the score is stale, a required feature becomes unreliable, or the pilot exceeds agreed limits, suppress recommendations. Carry on with manual triage, investigate with the data owner, and record the next release decision.

Review the [AI strategy](strategy.md) for selection criteria and [governance controls](governance.md) for required roles and evidence.
