# Frontend Data Contract (Draft)

**Job Hunting AI Web Tool | CS 467 Summer 2026**
**Owner:** Brian Merritt (frontend)
**Status:** Draft for review by Ethan (backend endpoint), Jawwad (analytics payload), and Chloe (retrieval layer / score format)
**Last updated:** 7/17/2026

This document defines the request the React frontend sends to the FastAPI backend and the response shape the UI requires. Every field the UI renders is listed here. If a field is renamed, removed, or changes type, the frontend breaks, so changes should be agreed before implementation.

**Priority key** (Brian's assessment, based on what blocks which milestone — open to team adjustment):

- **P1** — needed before or during Progress Report #2. Blocks the search form or results card.
- **P2** — needed before Progress Report #3. Tied to sorting, the chart, or ranking evaluation.
- **P3** — low priority. Safe to patch later without rework.

---

## 1. Endpoint

```
POST /api/search
Content-Type: application/json
```

**[P1]** Open question (for Ethan): confirm the path and whether search is POST with a JSON body or GET with query params. POST is assumed here because `skills` is a list and the payload is not URL-friendly.

**[P3]** Open question (for Ethan): when a search triggers the staleness check and the index is found stale, does this endpoint block until re-ingestion and re-embedding finish, or does it return current (possibly stale) results immediately while refresh happens in the background? This affects whether the frontend needs a long-wait loading state and whether the "fast response time" non-functional requirement is achievable on a stale hit.

---

## 2. Request

Sent by the search form on the home page.

```json
{
  "job_title": "machine learning engineer",
  "skills": ["python", "pytorch", "sql"],
  "location": "remote",
  "experience_level": "mid",
  "top_n": 20
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_title` | string | yes | Free text from the Job Title / Keywords input. May be empty string if the user only enters skills. |
| `skills` | string[] | no | Tag input. Empty array if none entered. |
| `location` | string | no | Free text. Defaults to `"remote"` if left blank. |
| `experience_level` | string | no | One of `"entry"`, `"mid"`, `"senior"`, or `""`. Proposed enum, open to change. |
| `top_n` | integer | no | Number of results requested. Frontend defaults to 20 if omitted. |

**[P3]** Open question (for Ethan): should the backend enforce a max on `top_n`, and what happens if all fields are empty? Proposal is a 400 with a readable error message rather than returning everything.

**[P1]** Open question (for Ethan / Jawwad): since RemoteOK is remote-only, what does `location` actually do? Options: it filters/boosts display for a preferred city, it gets folded into the semantic query text, or it's currently decorative and doesn't affect matching. This needs an answer or the field is ambiguous.

**[P1]** Open question (for Ethan / Brian): final `experience_level` values. Does the list need a tier beyond entry/mid/senior (for example "lead" or "staff")? Is "internship" separate from "entry"? What does an empty value mean, no preference, or should it be omitted from the request entirely? Are these the exact strings stored in the backend, or does the frontend send a human-readable label that gets translated?

---

## 3. Response

```json
{
  "query_echo": {
    "job_title": "machine learning engineer",
    "skills": ["python", "pytorch", "sql"],
    "location": "remote",
    "experience_level": "mid"
  },
  "match_count": 18,
  "index_last_updated": "2026-07-17T14:32:00Z",
  "results": [ /* JobResult objects, see below */ ],
  "analytics": { /* see section 5 */ }
}
```

| Field | Type | Notes |
|---|---|---|
| `query_echo` | object | The criteria the backend actually ran. Rendered in the search filter bar at the top of the results page. |
| `match_count` | integer | Number of results returned. Displayed next to the active criteria. **Ambiguous — see note below.** |
| `index_last_updated` | ISO 8601 string | Timestamp of the last successful ingestion. Supports a "last verified" indicator in the UI. Nullable if unknown. |
| `results` | JobResult[] | Ranked, highest score first. Empty array is valid and renders an empty state, not an error. |
| `analytics` | object | Data for the skill-frequency chart. See section 5. |

**[P2]** Open question (for Ethan): does `match_count` mean the total number of semantic matches found before capping, or just `results.length` (the number actually returned, capped by `top_n`)? These can differ, and the filter bar text ("X matches found") depends on which one it is.

**[P2]** Open question (for Ethan / Brian): is the Score/Recent sort toggle on the results page a client-side re-sort of the already-returned `results` array, or does it trigger a new backend request? The data needed is the same either way, but this hasn't been agreed and affects how the frontend implements the toggle.

---

## 4. JobResult object

One per job card. Field names map directly to the card layout in the UI/UX spec (Figure 5).

```json
{
  "id": "remoteok-1049283",
  "score": 0.8431,
  "title": "Senior Machine Learning Engineer",
  "company": "Acme Corp",
  "location": "Remote (US)",
  "salary": "$150,000 - $185,000",
  "role_type": "full-time",
  "date_listed": "2026-07-11T00:00:00Z",
  "description": "Plain text description with HTML already stripped.",
  "skills": ["python", "pytorch", "aws"],
  "apply_url": "https://remoteok.com/remote-jobs/1049283"
}
```

| Field | Type | Nullable | UI element |
|---|---|---|---|
| `id` | string | no | React key. Must be stable across requests. **See note on stability below.** |
| `score` | float | no | Score ring. See section 6 on format and precision. |
| `title` | string | no | Role heading |
| `company` | string | yes | Company line. Renders as "Company not listed" if null. |
| `location` | string | yes | Location line |
| `salary` | string | yes | Salary line. Hidden if null. **See note on formatting below.** |
| `role_type` | string | yes | Full-time / part-time / contract badge. Hidden if null. **See note on enum below.** |
| `date_listed` | ISO 8601 string | yes | "Listed X days ago". Also drives the Recent sort option. |
| `description` | string | yes | Card body. Must be plain text with HTML stripped by ingestion, not by the frontend. **See note on length below.** |
| `skills` | string[] | no | Skill tags. Empty array is fine. |
| `apply_url` | string | no | Apply link |

**[P1]** Open question (for Ethan / Chloe): does `id` map directly to RemoteOK's own posting ID, and does it stay stable across re-fetches? This matters because Chloe's upsert logic depends on stable IDs to avoid duplicates, and the frontend depends on the same stability for React keys — if IDs shift on refresh, cards can duplicate or lose position.

**[P1]** Open question (for Ethan): is `role_type` a fixed enum (for example `"full-time" | "part-time" | "contract"`), or is it free text passed through from whatever RemoteOK provides? If it's an enum, the exact allowed values need to be agreed so the frontend's badge rendering doesn't silently fail on an unexpected value.

**[P1]** Open question (for Ethan): does ingestion format `salary` into a display string like `"$150,000 - $185,000"`, or does it pass raw numeric min/max and the frontend formats it? Also unresolved: whether hourly vs. annual pay is distinguished, and how currency is handled if postings aren't all USD.

**[P3]** Open question (for Ethan): is there a max length on `description`? RemoteOK descriptions can be long. Unclear whether ingestion truncates before storage or the frontend truncates for card display.

**[P1]** Note on nullability (for Ethan): RemoteOK postings are inconsistent, so salary, role type, and company are frequently missing. The frontend handles nulls, but it needs `null` rather than an empty string or the string `"None"` so the conditional rendering works.

**[P2]** Note on `date_listed` (for Ethan): the Recent sort option in the UI/UX spec sorts by this field. If it is null for a meaningful share of postings, that sort degrades. Worth confirming what percentage of RemoteOK postings actually carry a usable date.

---

## 5. Analytics payload (chart data)

For Jawwad. Drives the skill-frequency bar chart with hover interaction.

```json
{
  "skill_frequency": [
    { "skill": "python", "count": 14 },
    { "skill": "aws", "count": 9 },
    { "skill": "docker", "count": 6 }
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `skill_frequency` | array | Pre-sorted descending by `count`. Frontend does not re-sort. |
| `skill_frequency[].skill` | string | Display label. Should be normalized casing (lowercase or title case, pick one and stay consistent). |
| `skill_frequency[].count` | integer | Number of matched postings containing that skill. Shown on hover. |

Open questions for Jawwad:
- **[P2]** How many entries should be returned? Proposal is top 10, computed server side, so the chart does not need to truncate.
- **[P2]** Are skill names normalized (for example "JS" and "JavaScript" collapsed)? Inconsistent naming is a known risk in the project plan and it shows up directly in this chart.
- **[P2]** Should this be computed over the returned `top_n` results only, or over a wider match set?

---

## 6. Score format

The score ring and the match score guide both depend on this.

Proposal: `score` is a float from 0.0 to 1.0 where higher is a better match, and the frontend renders it as a percentage.

**[P1]** This needs confirmation (owner: Chloe) because ChromaDB returns a **distance**, not a similarity, and for cosine distance lower is better. Whoever converts distance to similarity should do it once, server side, so the frontend never has to guess which direction the number runs. Proposal is that Chloe's retrieval layer does the conversion and returns a similarity.

**[P2]** Second open question (for Jawwad): score buckets for the match score guide. The frontend needs the thresholds that separate strong, moderate, and weak matches. These should not be invented in the frontend. Proposal is that Jawwad sets them from evaluation work and they are documented here once known.

**[P2]** Third open question (for Chloe / Jawwad): precision and rounding. Neither the raw `score` value nor its rounding for display has been specified. Proposal: backend sends a float with reasonable precision (e.g., 4 decimal places), and the frontend rounds to a whole-number percentage for display. Needs confirmation so both sides round consistently, especially near bucket boundaries in the score guide.

---

## 7. Errors

**[P3]** Owner: Ethan. Proposed shape for any non-200 response:

```json
{
  "error": "readable message for display",
  "detail": "optional technical detail for logs"
}
```

Cases the frontend needs to handle distinctly:
- Empty or invalid search criteria (400)
- Vector store unreachable (503)
- Ingestion failure with a stale index still usable (200 with results plus a warning flag, proposal below)

Proposal for the partial-failure case: return results as normal but include `"index_stale": true` at the top level so the UI can show a notice rather than an error.

---

## 8. Open items summary

Sorted by priority. See the priority key at the top of this document.

| Priority | Item | Owner | Status |
|---|---|---|---|
| P1 | Score direction (similarity vs distance) | Chloe | Open |
| P1 | Endpoint path and method | Ethan | Open |
| P1 | `experience_level` enum values | Ethan / Brian | Proposed |
| P1 | `location` semantics (filter, boost, query text, or decorative) | Ethan / Jawwad | Open |
| P1 | `role_type` enum vs. free text | Ethan | Open |
| P1 | Salary formatting (string vs. raw numbers, currency, hourly/annual) | Ethan | Open |
| P1 | `id` source and stability across re-fetches | Ethan / Chloe | Open |
| P1 | Null handling for salary / company / role_type | Ethan | Proposed |
| P2 | `match_count` definition (total matches vs. returned count) | Ethan | Open |
| P2 | Sort toggle: client-side re-sort vs. new request | Ethan / Brian | Open |
| P2 | `date_listed` coverage (share of postings with usable dates) | Ethan | Open |
| P2 | Score bucket thresholds for the guide | Jawwad | Open |
| P2 | Score precision and rounding | Chloe / Jawwad | Proposed (4 decimals, frontend rounds to whole %) |
| P2 | Skill name normalization | Jawwad | Open |
| P2 | Number of skills in chart payload | Jawwad | Proposed (top 10) |
| P2 | Analytics scope (top_n results vs. wider match set) | Jawwad | Open |
| P3 | Blocking vs. background refresh on stale index | Ethan | Open |
| P3 | `top_n` max cap and empty-criteria behavior | Ethan | Proposed (400 error) |
| P3 | `description` max length and truncation owner | Ethan | Open |
| P3 | Error response shape | Ethan | Proposed |

**Count by priority:** P1 = 8, P2 = 8, P3 = 4.

**Count by owner** (joint items counted for each person): Ethan = 16, Chloe = 4, Jawwad = 7, Brian = 2.