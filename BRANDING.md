# SaFe brand guide

## Source and status

Based on the team's [project notes and build prompts](https://docs.google.com/document/d/1bNgqXvLrVUD0cKjE_3u92J4tO1wbgkOCv7hBx2KxQjs/edit?tab=t.dca2et6zltrd), read November 3, 2026. The prompts tab defines the current product direction; the idea tab records earlier exploration. The positioning and tagline below follow the doc. Visual choices are starter defaults introduced by this guide, and can be revised by the team.

## Identity

- **Name:** SaFe. Preserve this capitalization in product copy; use `safe` for code identifiers when needed. Do not invent an expanded acronym.
- **Tagline:** Report it once, and it counts.
- **One sentence:** SaFe brings matching neighborhood reports together so San Francisco residents are heard and city agencies receive one clear signal.
- **Short pitch:** Residents describe a problem and its location. Mistral classifies the report and helps check whether it describes an existing issue; Elasticsearch finds nearby matches. SaFe groups matching reports, drafts a consolidated agency email at 10 reports, and generates updates when the issue is resolved.
- **Audience:** San Francisco residents first; city agency staff and community organizations second.
- **Personality:** Neighborly, calm, practical, transparent, and hopeful.

## What we promise

Every report contributes to a shared picture. Residents can understand whether an issue is newly recorded, already gathering reports, ready for escalation, or resolved. Agencies can see the location, summary, and report count together.

Explain the prototype honestly: emails and notices are generated or printed in the demo. They are not delivered to residents or the city. Never imply official city affiliation, guaranteed response times, verified safety, or automatic municipal resolution.

## Voice and terminology

Use short sentences, familiar words, and specific next steps. Thank residents for contributing. Describe observable issues without blaming people or labeling neighborhoods as dangerous. A report count measures reports, not independent verification, unique residents, or objective urgency.

| Term | Meaning |
| --- | --- |
| Report | One resident submission |
| Issue | The shared problem that matching reports belong to |
| Report count | Submissions attached to an issue |
| Escalation draft | A consolidated message generated for the responsible agency |
| Resolved | The issue has explicitly been marked resolved; this is not an AI inference |

Avoid technical terms such as geo deduplication, indexing, and model confidence in resident-facing messages. Keep Mistral and Elasticsearch attribution in technical demos and project descriptions.

## Product copy

| Moment | Example |
| --- | --- |
| New issue | Thanks. Your report started a new issue for this location. |
| Matching issue | Your report was added to this issue. It now has 6 reports. |
| Threshold reached in demo | This issue has 10 reports. A consolidated message to the responsible agency is ready to review. |
| Already escalated in demo | This issue already has an escalation draft. Thanks for checking in. |
| Resolution notice in demo | This issue has been marked resolved. Thank you for reporting it and helping improve your neighborhood. |
| Missing location | Add a location so we can check for nearby reports. |
| Unclear description | Please describe the problem and where it is. |
| Service unavailable | We couldn't process your report right now. Please try again. |

The source doc's phrase “already reported to the city” describes the eventual delivery experience. Use it only once a real integration confirms successful delivery. For the prototype, say “escalation draft” or “message ready.”

## Visual defaults

Keep the identity lightweight: a clear wordmark and a small set of reusable tokens are enough. The user subsequently requested a polished Person B workspace; use these defaults for its local UI.

| Token | Value | Use |
| --- | --- | --- |
| `brand` | `#0F766E` | Primary actions and wordmark |
| `brand-strong` | `#115E59` | Hover and active actions |
| `ink` | `#142D32` | Main text |
| `muted` | `#52666B` | Supporting text |
| `canvas` | `#F6F8F7` | Page background |
| `surface` | `#FFFFFF` | Cards and panels |
| `border` | `#D6E0DD` | Dividers and noninteractive boundaries |
| `attention` | `#9A3412` | Threshold and review labels |
| `success` | `#166534` | Resolved labels |
| `error` | `#B91C1C` | Errors |

Use white text on solid brand buttons. Use ink for normal body text. Verify contrast in the actual interface, including focus states and map labels; pale borders alone should not identify interactive controls.

- **Type:** System sans-serif stack: `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`. No font download is required. Use monospace only for code and technical identifiers.
- **Scale:** 16px body, 14px supporting text, 24–32px headings; approximately 1.5 body line height.
- **Layout:** 8px spacing rhythm, generous whitespace, 12px panel radius, restrained shadows.
- **Mark:** Start with the SaFe wordmark. Any later symbol should suggest a location and shared contribution. Avoid police badges, alarm imagery, and imagery implying guaranteed protection.
- **Status:** Always pair color with text or an icon. Provide visible keyboard focus and accessible labels.
- **Maps, if later added:** Label layers as reported issues, show time windows and sources, and avoid presenting report density as a neighborhood safety score.

## Scope and presentation

Lead the demo with a measured count of SF311 cases whose notes mention duplicates. State the actual query scope and timestamp; do not invent a statistic or imply those cases represent every duplicate in the city.

Show the core loop: ten descriptions become one issue and one draft; an eleventh submission sees the existing escalation; a different nearby problem stays separate; resolution generates notices.

Cleanup photos, points, leaderboards, neighborhood recommendations, private social feeds, and weekend meetups are future ideas. Do not present them as implemented features. Use synthetic reporter identities in screenshots and public examples.
