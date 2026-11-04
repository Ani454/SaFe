# SaFe: judging context and demo strategy

## Verified event context

The organizer's [hack-night repository](https://github.com/jdarmada/elastic-mistral-hacknight#judging-criteria-and-presentations), supplied by the user and checked November 3, 2026, publishes three criteria: **Novelty**, **Use of Elastic**, and **Use of Mistral**. No numerical weights are listed. Both technology portions must appear in the demo. The initial pitch is two minutes; selected finalists receive a timed three-minute presentation. A polished UI is unnecessary; Agent Builder is optional and described as a bonus.

This supersedes the earlier provisional assessment based on the [Luma event page](https://luma.com/mistral-elastic), which did not list the rubric. The recommendations below apply the published criteria to SaFe; they are not additional organizer requirements.

## Criterion-to-proof plan

| Published criterion | SaFe's argument | Proof to prioritize | Current gap |
| --- | --- | --- | --- |
| Novelty | A shared physical-issue record accumulates reports into one reviewable escalation, while nearby distinct objects remain separate. | Show a paraphrase merge, a same-category different-object rejection, and the tenth/eleventh-report behavior. | The full lifecycle remains an integration target in this checkout. |
| Use of Elastic | Retrieval constraints and stored history determine which issue can receive a report and what the consolidated draft contains. | Show the actual geo query, mapping, candidate ID, and persisted issue before/after aggregation. | Storage and retrieval are owned by Person A and absent here. |
| Use of Mistral | Language understanding affects classification, the merge decision, and the factual consolidated message. | Show live structured classification and match decisions, then a draft tied to the stored issue. | Mocked parsing tests and sample previews do not establish live quality. |

Our recommendation: spend remaining effort on one integrated example with visible query and model outputs. Use the existing UI as a presentation surface when helpful; avoid expanding it while these proof gaps remain. No criterion requires adding an agent or embeddings.

The user's clarified [product vision](PRODUCT_VISION.md) adds NGO action, reviewed completion photos, and contributor recognition. This gives SaFe a broader purpose beyond reporting. Introduce it as the roadmap until demonstrated; a planned leaderboard is not implementation evidence. Ten reports mean the workflow threshold was reached, not that AI verified an incident.

## Novelty risk: go beyond the starter idea

The organizer's [open challenge](https://github.com/jdarmada/elastic-mistral-hacknight/blob/main/open_challenge.md) already suggests a 311 assistant that classifies descriptions and finds similar nearby open cases. Presenting only those operations leaves SaFe close to a supplied example.

Our proposed distinction is the combination of conservative physical-issue identity, retained report history, one threshold draft, and explicit resolution notices. Demonstrate that distinction with a mattress and a separate dumped cabinet nearby: both are illegal dumping, but they must not become the same issue. Then show differently worded descriptions of the mattress converging on one record. This is a concrete technical contribution; do not claim the overall concept is unprecedented without a broader comparison.

If match confirmation is cut under the existing time-slip policy, explicitly withdraw the different-object guarantee and narrow the novelty claim. Do not describe radius/category matching as object-level understanding.

## The story judges should remember

**Ten descriptions of one blocked sidewalk should become one clear issue and one reviewable agency draft. A different problem nearby must stay separate.**

SaFe helps a resident understand whether their report concerns an existing neighborhood issue, while preserving a shared record of what people reported. Its proposed operational benefit is less fragmented information for agency review. That benefit is a hypothesis until measured with users or agency staff; the prototype does not prove faster repairs or reduced city workload.

Suggested opening:

> Imagine ten neighbors describing the same discarded mattress in ten different ways. SaFe brings those reports into one issue. Elasticsearch finds the nearby candidate; Mistral checks whether the descriptions refer to the same physical problem. At ten reports, SaFe prepares one consolidated agency message for review.

Use a measured SF311 duplicate-mention count before this opening only when the query and result are available. Otherwise introduce the mattress as a synthetic demonstration, without a citywide statistic.

## Make both technologies necessary and visible

| Component | Responsibility in the agreed design | Evidence to show |
| --- | --- | --- |
| Elasticsearch | Retrieve the nearest eligible issue using category, 50-meter radius, 14-day creation window, and unresolved status; retain report history and lifecycle state. | Actual `issues` mapping, query, returned candidate with ID, and stored record before/after the tenth report. |
| Mistral | Structure varied resident wording; conservatively confirm physical-issue identity; draft messages from supplied issue facts. | Actual request inputs and validated classification, structured match boolean, and generated draft. Exclude credentials and reporter contact details. |
| Shared pipeline | Apply lifecycle rules: attach reports, retain one threshold draft, recognize an existing escalation, and generate resolution notices once. | One issue with ten reports and one retrievable draft; eleventh matching report leaves the count unchanged; explicit resolution produces ten notices. |

Elasticsearch bounds the candidate set; Mistral handles ambiguity in language. Category and distance alone cannot distinguish two discarded objects on the same block. Mistral alone cannot retrieve and maintain the authoritative issue record. This division is the technical argument for the combined stack.

The MVP retrieves one nearest candidate. If Mistral rejects it, create a new issue; do not imply that all nearby candidates were searched. Keyword/vector/hybrid search are mentioned on the event page, but this checkout does not implement them. Do not add or claim them solely for sponsor visibility. Any future retrieval extension needs a coordinated contract change and measured benefit.

## Two-minute initial demo

Prepare a repeatable fixture runner or pre-stage the first nine reports so the threshold moment fits. Any preloaded or recorded state must be labeled. The following timing is our rehearsal plan within the organizer's two-minute initial slot.

| Time | Show | What it establishes |
| --- | --- | --- |
| 0:00–0:15 | Resident problem and synthetic mattress scenario; measured SF311 evidence only if available. | A specific local beneficiary and an honest problem statement. |
| 0:15–0:45 | A paraphrased report; Mistral classification; Elasticsearch candidate/query; Mistral match decision. | Both technologies contribute to the same working flow. |
| 0:45–1:05 | A dumped cabinet 30 meters away, with an explicit distinguishing description. | Same category and proximity do not force a false merge. |
| 1:05–1:40 | Tenth mattress report, persisted count and consolidated draft, then an eleventh matching report. | Aggregation, useful output, and no duplicate escalation artifact. |
| 1:40–2:00 | Name the stored facts behind the draft, label live versus preloaded/mock behavior, and close with the resident benefit. | A clear result and an inspectable technical contribution. |

For the three-minute finalist presentation, retain this core and use the extra minute for explicit resolution, ten generated notices, repeat-resolution behavior, and measured SF311 evidence if available. Rehearse provider latency; use clearly labeled captured outputs if a live sequence cannot fit. Keep the full acceptance suite for verification rather than attempting every edge case on stage.

If only the Person B workspace is available, demonstrate classification, comparison, and drafts as separate tools. State that storage and lifecycle integration are pending. A manually entered example issue is not a retrieved Elasticsearch record.

## Evidence and implementation priorities

1. **Integrate the existing contracts first.** Person A supplies real retrieval/storage; Person B supplies Mistral functions; Person C wires the shared lifecycle. Agree on draft persistence, retries, and notification history before cross-file changes. UI polish cannot substitute for this integration.
2. **Prove the difficult distinction.** Evaluate same-object paraphrases and same-category different-object pairs, alongside vague input, invalid coordinates, old/outside-radius candidates, and model failures. Keep fixed synthetic inputs and expected outcomes. Record observed results rather than claiming accuracy from mocked tests.
3. **Capture a reproducible live run.** Save the run timestamp, model name, fixture version or commit, query/mapping, returned issue IDs, and outputs. Record latency per stage if measured. Separate live outcomes from fixture tests and sample previews; do not publish secrets or personal data.
4. **Measure narrowly.** For SF311 evidence, save the actual field mapping, duplicate-mention query, time window, matched count, denominator if reporting a percentage, and run timestamp. Notes mentioning duplicates are not a ground-truth measure of duplicate physical issues. Ten synthetic reports becoming one issue is demo behavior, not a measured 90% reduction in city workload.
5. **Demonstrate failure recovery.** A failed match must not merge reports. A failed draft must leave escalation retryable. If the integrated implementation supports only serial submissions, state that limitation rather than claiming concurrent exactly-once behavior.

## Current evidence boundary

On the active Person B branch, the checkout contains `mistral_ai.py`, `ui_server.py`, `web/`, and mocked tests. It does not contain `es_store.py`, `pipeline.py`, or `demo.ipynb`. Shared `origin/main` at `b34c6e8` additionally contains a Streamlit SF311 map/statistics app in `app.py`, with Elasticsearch queries and Mistral summarization. That code was inspected without running it; neither live deployment nor the intended submission/reward lifecycle was verified. No live Mistral/Elasticsearch integration run or measured SF311 duplicate count was performed for this strategy update. The workspace's sample previews are illustrative fixtures, not model calls.

Keep this section current as integration evidence lands. All messages remain drafts; no city submission or email delivery is implemented. The ten-report threshold is a demo rule for ordinary service requests, not evidence of urgency, ten unique people, or an emergency response policy.

## Closing line

> SaFe turns scattered neighborhood reports into a shared issue and a clear next step: one consolidated message ready for review. Elasticsearch supplies the relevant record; Mistral makes the language useful.

The next external validation is a review with residents and agency staff: do the grouped issue and draft preserve the details they need? Describe city delivery, operational savings, and broader deployment as future work until verified.
