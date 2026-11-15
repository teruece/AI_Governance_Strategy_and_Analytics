# AI use-case and risk register

## Use-case record

| Field | Example entry |
| --- | --- |
| ID and status | AI-001 · Portfolio sandbox using synthetic data |
| Use case | Flag service-desk tickets for analyst review at ticket creation if their estimated risk of breaching the resolution SLA is high. |
| Decision and authority | The analyst applies the existing priority and SLA policy. The shift supervisor owns escalation and feedback. |
| Affected users | Support analysts and requesters waiting for a response or resolution. |
| Data | Synthetic creation time, queue, priority, backlog and SLA hours. Generated resolution outcomes support retrospective evaluation. |
| Worth testing | Earlier identification of tickets that need review, weighed against unnecessary alerts and review capacity. |
| Fallback | Standard queue and SLA review for any ticket without a usable signal, and manual triage when scoring is paused. |
| Accountable owner | Service operations owner. The model owner maintains reproducibility. Independent reviewer challenges the pilot evidence. |
| Current evidence | Executable dataset and evaluation in [the implementation](implementation.md). Owners and live controls in this register are illustrative. |
| Proposed live scope | Begin with approved queues during staffed hours. Review the pilot after the expected resolution outcomes mature. Record the next decision before expanding. |

## Risk and control record

Ratings describe residual concern for a hypothetical live pilot. Sandbox evidence records what the repository can demonstrate. Live controls require an owner and evidence before pilot release.

| ID | Risk and consequence | Proposed control and evidence | Residual concern and owner | Trigger and response |
| --- | --- | --- | --- | --- |
| R-01 | **Time leakage.** A feature becomes available only after ticket creation, inflating offline performance and creating an unusable score. | Verify timestamp and lineage for each candidate feature, keep outcomes separate, and reproduce the chronological evaluation on a frozen snapshot. Sandbox uses gapped time splits and fits only on the training period. | High · Model owner | A late or untraceable input invalidates the evaluation. Pause release, remove or repair the feature and rerun the evaluation. |
| R-02 | **Missed urgent cases.** A queue with fewer examples or different policy may have more missed breaches. | Compare missed-breach rates, sample sizes and false positives by eligible queue. Review missed cases and extend the data window where evidence is sparse. Sandbox reports diagnostic metrics for its three queues. | High · Independent reviewer | A sustained gap or pattern of missed critical cases triggers manual review of the affected queue and a release reassessment. |
| R-03 | **Alert overloading.** Review demand can displace routine triage. | Compare thresholds against staffed review capacity and compare shadow alert counts with actual analyst workload. Define a clear owner for each alert. | Medium · Service operations owner | Two shifts above the approved limit trigger a staffing or scope decision before any threshold revision. |
| R-04 | **Overreliance on score.** Staff may treat a suggestion as an authoritative priority or confuse an unavailable score with low risk. | Use a separate review presentation, make unscored status explicit, train analysts and record the analyst's final action and reason. | High · Shift supervisor | Misrouted or wrongly dismissed cases prompt signal suspension for the affected team and review of decisions made in the affected period. |
| R-05 | **Uncontrolled data access.** Real ticket records can carry confidential content, whether in a feature, an export or an audit trail. | Use an approved feature whitelist, restrict the score and audit views, check permissions with representative roles, and set agreed retention. Sandbox uses generated data. | High · Data steward | An unauthorised view or disclosure triggers containment, a documented incident and access revalidation before restart. |
| R-06 | **Change in policy or workload.** A new queue, deadline policy or backlog regime can make the old threshold unsuitable. | Version the feature and label contract, reserve a fallback for unsupported scope, verify validity by queue and repass release gates after material changes. | High · Model owner | An unapproved schema or label change pauses the signal. Investigate and evaluate before resuming. |
| R-07 | **Outcome delay.** Precision or recall computed before deadlines mature can be misleading. | Record the label cutoff and publish mature-sample counts with operational metrics. Exclude cases still inside their observation window from outcome measures. | Medium · Analytics product owner | A stale or incomplete outcome feed suppresses the performance reading until reconciled. |

See the [operating model](governance.md) for the release, monitoring and rollback workflow.
