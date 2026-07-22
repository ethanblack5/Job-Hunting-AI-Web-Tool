# Frontend Data Contract (Draft)

**Job Hunting AI Web Tool | CS 467 Summer 2026**
**Owner:** Brian Merritt (frontend)
**Status:** In use. Core shapes agreed with Ethan (backend), Chloe (retrieval layer), and Jawwad (analytics payload). Remaining open items are listed in section 8.
**Last updated:** 7/19/2026

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

Search is a POST with a JSON body rather than a GET with query params, because `skills` is a list and the payload is not URL-friendly.

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
| `experience_level` | string | no | One of `"internship"`, `"entry"`, `"mid"`, `"senior"`, `"lead"`, `"staff"`, `"principal"`, or `""`. |
| `top_n` | integer | no | Number of results requested. Frontend defaults to 20 if omitted. |

**[P3]** Open question (for Ethan): should the backend enforce a max on `top_n`, and what happens if all fields are empty? Proposal is a 400 with a readable error message rather than returning everything.

`location` is the company's HQ location, not a remote-eligibility field, since RemoteOK postings are remote regardless. It is folded into the semantic query text rather than used as a hard filter.

**[Open, for Ethan / Brian]** Because a user searching "remote, Austin" is matching against company HQ rather than where they can actually work, it is worth deciding whether this field earns a place as a search input, or whether it should be relabeled so it does not imply something it cannot deliver.

The frontend sends the `experience_level` strings above exactly as listed, with no translation layer, and the dropdown orders them lowest to highest experience so internship appears first.

**[Open, for Ethan]** Whether an empty `experience_level` should be sent as `""` meaning "no preference," or omitted from the request entirely.

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

`id` must be unique and must persist across re-fetches. Chloe's upsert logic depends on it to update a posting in place rather than duplicate it, and the frontend depends on the same stability for React keys.

**[Open, for Ethan]** What the ID is built from. Ethan proposed the last segment of the RemoteOK URL path, which combines the numeric ID with the position and company name. That slug changes if an employer edits the job title, which breaks persistence and creates duplicates. Counter-proposal: RemoteOK's raw `id` with a source prefix, e.g. `remoteok-1049283`, which stays stable across re-fetches and will not collide once a second data source is added. Either way, RemoteOK's `id` needs confirming as genuinely unique.

RemoteOK does not provide `role_type` as a structured field. It appears only inconsistently inside free-text descriptions, so it will be null for most postings.

**[Open, for Ethan / Brian]** Whether to build a parser that extracts role type from description text, or to accept it as usually-null and hide the badge when absent. Leaning toward the latter, since the extraction effort is hard to justify for a single badge.

`salary` arrives as a formatted display string built by ingestion, e.g. `"$120,000 - $150,000"`, rather than raw numeric min/max. The frontend renders it as-is and does no formatting.

**[Open, for Ethan]** Whether hourly and annual pay are distinguished in that string, and how currency is handled if postings are not all USD.

**[P3]** Open question (for Ethan): is there a max length on `description`? RemoteOK descriptions can be long. Unclear whether ingestion truncates before storage or the frontend truncates for card display.

Missing fields arrive as real JSON `null`. Python `None` serializes to `null` automatically through FastAPI and Pydantic, so no extra handling is needed on either side, and the frontend's conditional rendering can rely on it directly. Worth one sanity check against a live endpoint to confirm the response body shows `null` rather than the string `"None"`.

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
- **[P2]** Are skill names normalized (for example "JS" and "JavaScript" collapsed)? Inconsistent naming is a known risk in the project plan and it shows up directly in this chart. Partial answer from Ethan's ingestion PR (#39): `process_job` already lowercases, trims, and dedupes tags. That handles casing and duplicates but not synonyms, so the collapsing question is still open.
- **[P2]** Should this be computed over the returned `top_n` results only, or over a wider match set?

---

## 6. Score format

The score ring and the match score guide both depend on this.

`score` is a similarity from 0.0 to 1.0 where higher is a better match. The frontend multiplies by 100 to render the percentage in the score ring.

ChromaDB returns a distance by default, where lower is better. The retrieval layer converts distance to similarity before the value leaves the backend, so the frontend never has to reason about which direction the number runs.

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

Sorted by priority. See the priority key at the top of this document. Settled decisions are written into the sections above rather than tracked here.

| Priority | Item | Owner | Status |
|---|---|---|---|
| P1 | `id` format (raw ID + source prefix vs. URL slug) | Ethan | Open |
| P1 | Is `location` worth surfacing as a search input | Ethan / Brian | Open |
| P1 | `role_type`: parse from description or accept as usually-null | Ethan / Brian | Open |
| P1 | Salary string: hourly vs. annual, non-USD currency | Ethan | Open |
| P1 | Empty `experience_level`: send `""` or omit | Ethan | Open |
| P2 | `match_count` definition (total matches vs. returned count) | Ethan | Open |
| P2 | Sort toggle: client-side re-sort vs. new request | Ethan / Brian | Open |
| P2 | `date_listed` coverage (share of postings with usable dates) | Ethan | Open |
| P2 | Score bucket thresholds for the guide | Jawwad | Open |
| P2 | Score precision and rounding | Chloe / Jawwad | Proposed (4 decimals, frontend rounds to whole %) |
| P2 | Skill synonym collapsing (casing/dupes already handled at ingestion) | Jawwad | Open |
| P2 | Number of skills in chart payload | Jawwad | Proposed (top 10) |
| P2 | Analytics scope (top_n results vs. wider match set) | Jawwad | Open |
| P2 | Field naming: `date_listed` vs. `date_posted` | Ethan / Brian | Open |
| P3 | Blocking vs. background refresh on stale index | Ethan | Open |
| P3 | `top_n` max cap and empty-criteria behavior | Ethan | Proposed (400 error) |
| P3 | `description` max length and truncation owner | Ethan | Open |
| P3 | Error response shape | Ethan | Proposed |

None of the remaining P1 items block frontend work. Each is a refinement to a decision that is already made.