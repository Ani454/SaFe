# SaFe: community action and recognition

## User direction, November 3, 2026

SaFe is intended to help San Francisco residents, NGOs, and local authorities move neighborhood problems from reports to completed work, with recognition for people who contribute to the solution. The user clarified that gamification, completion photos, a contributor leaderboard, and community participation belong in the product vision. These are planned capabilities, not claims about the current build.

**Proposed positioning:** SaFe connects neighborhood reports to community action, tracks the outcome, and recognizes the people who help.

The user's reference to dates and people joining is provisionally interpreted as scheduled volunteer activities attached to an issue. Exact event details remain open; do not infer an unrelated feature from the ambiguous wording.

## Intended journey

| Step | Intended experience | Evidence or rule needed |
| --- | --- | --- |
| Report | A resident describes a problem, such as a broken streetlight, and supplies a location. | Valid location, original description, and recorded time. |
| Group | Elasticsearch finds an eligible nearby issue; Mistral checks whether the descriptions identify the same physical problem. | Preserve distinct objects even within the same category and radius. AI proposes identity, not factual verification. |
| Escalate | At ten attached reports, prepare a consolidated agency message. Later residents see that an escalation already exists. | Ten reports trigger the workflow; they do not prove truth or ten independent witnesses. The current MVP generates a draft. Future delivery needs a real integration and a recorded successful send before displaying “sent.” |
| Coordinate | NGOs or residents discover relevant open issues and propose an appropriate contribution. | Agency-owned repairs, including streetlight electrical work, stay with the responsible organization; community activities can address suitable cleanup work or coordination. |
| Participate | An organizer proposes a dated volunteer activity; people join and coordinate around the issue. | Proposed details: issue link, organizer, time, meeting location, participant list, and activity status. This is a product proposal, not an existing contract. |
| Submit completion | A contributor uploads an after photo and a description of the work. | Treat this as a completion claim awaiting review. A photo or AI comparison alone does not establish that the right issue was fixed. |
| Review and resolve | A designated reviewer or responsible organization accepts or rejects the completion claim. | Record the decision, actor, time, issue, and supporting evidence. Define reviewer authority before implementation. Resolution must be explicit. |
| Recognize | Approved contributions earn points or awards and appear on a contributor leaderboard. | Reward accepted work, with one award per approved contribution. Define shared credit, reversals, and point values before implementation. |
| Update | Original reporters can see the recorded outcome and receive an update. | Current MVP generates notices only. Future delivery and subscriptions require separate implementation. |

## Make the game reward useful work

Reward reviewed contributions rather than repeated reporting. Otherwise, users could earn points by duplicating submissions or claiming work with an unrelated photo. Keep a record linking each award to a contribution, issue, review, and recipient so retries cannot award it twice. Rejecting or reversing a completion claim should also support reversing its award.

Leaderboards recognize contributors, not neighborhood safety or objective impact. Ten reports remain a count of submissions; identity checks and independent corroboration are separate concerns. Do not convert report counts or model certainty into “AI knows this is true.”

Mistral could later help describe before/after evidence and flag mismatches for a reviewer. That requires a separate image workflow and evaluation; the current text functions do not perform photo verification. Elasticsearch could later retrieve actionable issues and aggregate approved contributions for leaderboard views. Those are proposed extensions, not current mappings or measured outcomes.

## Build and demo boundaries

1. **Existing Person B branch:** text classification, comparison, agency drafts, resolution drafts, local UI, and mocked tests.
2. **Shared `main` observed at `b34c6e8`:** `app.py` implements a Streamlit SF311 map with geo/time queries, aggregations, and a Mistral summary; `data/` contains supporting data scripts. This was source inspection, not a live deployment or service verification. It does not establish that all intended functionality is online.
3. **Agreed core integration target:** submitted reports become persistent issues with the ten-report draft workflow, existing-escalation behavior, and explicit resolution notices. Keep the existing Python contracts and `open` / `escalated` / `resolved` status vocabulary until owners agree on extensions.
4. **Clarified product expansion:** NGO discovery, scheduled activities, joining, completion uploads and review, awards, and contributor leaderboards. These are in the product direction but have not been implemented by this context update. Add separate contribution/review/event/reward records only after agreeing on ownership and storage contracts.

The repository is [Ani454/SaFe](https://github.com/Ani454/SaFe). Inspect the relevant branch before making implementation claims; the active Person B branch and shared `main` contain different work. Do not overwrite another workstream or silently merge its code while updating the vision.

## Judging presentation

Lead with the working combined Elasticsearch–Mistral flow. Explain the larger purpose as a path from reporting to community contribution and recognition. If an NGO completion/reward screen is illustrative, label it as a proposed workflow. A planned leaderboard contributes to the story; only demonstrated behavior supports an implementation claim.

For a future community-action demo, a cleanup scenario makes the contributor journey clearer than volunteers repairing a streetlight. Keep the broken-streetlight example for agency escalation and status tracking. Preserve the two-minute core demo in [JUDGING.md](JUDGING.md); do not crowd out the actual queries and model decisions with roadmap screens.

## Implementation update

The user's full-site request authorizes and implements the reporting-to-community-action journey in website.py, backed by store.py, pipeline.py, and es_store.py. Activities, membership, completion evidence, admin review history, configurable point awards/reversals, profiles, leaderboard, and per-reporter generated notices now have persistent records and shared pages. Review is manual and resolution is explicit. They are application behavior, with external Mistral and Elasticsearch integration still requiring a credentialed live run. The earlier branch-state inventory above describes the pre-integration baseline. Deployment evidence and limits are in DEPLOYMENT.md.
