# Quant Job Crawler Design

Date: 2026-05-20

## Goal

Build a local application that crawls official company career pages for junior-friendly front quant jobs, stores job descriptions locally, classifies each role with Codex/LLM review, and helps track the application process.

The crawler is for a candidate with 1 year of work experience who holds H-1B status. The system should use a relaxed junior bar, collect broadly, and let later review layers make the nuanced decisions.

## Scope

V1 crawls live job postings only from official company career pages. It targets US jobs open to New York, Boston, Florida, New Jersey, or Chicago.

The firm universe focuses on quant-career-relevant firms:

- Quant hedge funds and systematic funds
- Multi-manager platforms with serious quant hiring
- Prop trading, market making, and HFT firms
- A small set of sell-side desks only when they are well known for quant careers

Quant sub-brands or business units are independent crawler targets only when they expose a separate official job posting page. Otherwise, they are treated as aliases under the parent company.

## Role Model

The system has three cooperating roles.

### Crawler

The crawler visits official career pages, collects job cards and job descriptions, applies broad negative filters, and stores coarse relevant postings.

The crawler should not try to prove that a job is relevant. Its job is to remove obvious noise while keeping ambiguous front-office roles for later evaluation.

### Evaluator

The evaluator reads stored job descriptions and classifies each role.

It labels:

- `front`
- `h1b`
- `exp`
- `score`
- `reason`
- `flags`

The evaluator uses the full job description, not just the title. It should support firm-specific aliases, such as Hudson River Trading using `Algorithm Developer` for a quant researcher style role.

### Policy Maker

The policy maker oversees the pipeline and updates policy files based on collected data, false positives, false negatives, and review decisions.

It should improve:

- hard noise filters
- H-1B eligibility guidance
- experience-level guidance
- front quant decision rules
- firm-specific title aliases

It should avoid making the crawler too aggressive unless there is strong evidence that a pattern is consistently irrelevant.

## Policy Files

Use markdown policy files so behavior stays editable and reviewable.

```text
policies/
  shared.md
  crawler.md
  evaluator.md
  policy_maker.md
```

`shared.md` is the source of truth. It defines the target locations, company aliases, field meanings, colors, examples, and known edge cases.

`crawler.md` instructs the crawler to crawl broadly, use only broad negative filters, and preserve ambiguous jobs.

`evaluator.md` instructs the LLM/Codex layer how to classify each stored job description.

`policy_maker.md` instructs the policy maker how to review results and propose or apply policy updates.

The application loads `shared.md` plus the role-specific file for each pipeline step.

## Classification Fields

Use concise field names.

- `front`: `green | red`
- `h1b`: `green | yellow | red`
- `exp`: `green | red`
- `score`: integer from `0` to `100`
- `reason`: concise explanation
- `flags`: compact tags
- `review`: `pending | approved | rejected | needs_review`

`front=green` means the role appears to be a front quant role: Quant Researcher, Alpha Researcher, Quant Trader, Algorithmic Trader, or a firm-specific front alpha alias.

`front=red` means the role is not a target front quant job. Examples include risk quant, execution quant, model validation, portfolio analytics, generic software engineering, data engineering, operations, compliance, legal, HR, sales, client service, or other non-front-office jobs.

`h1b=green` means the role appears adequate for an H-1B holder.

`h1b=yellow` means work authorization is unclear.

`h1b=red` means the posting explicitly requires US citizenship, permanent residency, a green card, or no sponsorship in a way that makes the role unsuitable.

`exp=green` means the role is reasonable to apply to with 1 year of work experience under a relaxed bar.

`exp=red` means the role is clearly too senior or otherwise unsuitable. Examples include VP+ bank roles, PM-only roles, team lead/head roles, explicit 5+ year requirements, or requirements that clearly exceed a junior candidate profile.

## Data Model

Use SQLite for V1.

### `companies`

- `id`
- `name`
- `group`
- `career_url`
- `ats`
- `active`
- `notes`

### `jobs`

One row per discovered official job posting.

- `id`
- `company_id`
- `company`
- `title`
- `loc`
- `url`
- `source`
- `jd`
- `jd_hash`
- `status`
- `first_seen`
- `last_seen`
- `closed_at`
- `crawl_note`

`status` values: `new`, `live`, `closed`, `ignored`.

### `evals`

One row per evaluator run. Evaluations are append-only so policy changes can be audited.

- `id`
- `job_id`
- `front`
- `h1b`
- `exp`
- `score`
- `reason`
- `flags`
- `model`
- `policy_ver`
- `created_at`

### `reviews`

Manual or policy-maker review decisions.

- `id`
- `job_id`
- `decision`
- `note`
- `reviewer`
- `created_at`

`decision` values: `approve`, `reject`, `needs_review`.

### `apps`

Application tracking.

- `id`
- `job_id`
- `app_status`
- `deadline`
- `priority`
- `applied_at`
- `contact`
- `note`
- `updated_at`

`app_status` values: `not_started`, `ready`, `applied`, `interview`, `rejected`, `offer`, `closed`.

## Pipeline

1. Load company seeds from config or database.
2. Crawl official career pages and collect job cards: title, location, URL, source.
3. Apply broad negative filters to remove obvious noise.
4. Fetch each remaining job description.
5. Store new or changed postings in `jobs`.
6. Deduplicate by canonical URL and `jd_hash`.
7. Re-evaluate jobs when the JD changes or the policy version changes.
8. Run evaluator with `shared.md` and `evaluator.md`.
9. Store evaluator output in `evals`.
10. Show jobs in the dashboard based on latest evaluation and review state.
11. Run policy maker periodically to update or propose policy improvements.

Rejected jobs should remain stored because they are useful examples for improving policy.

## Dashboard

The dashboard should be compact and workflow-oriented.

### Jobs

Default table for scanning collected positions.

Columns:

- company
- title
- loc
- front
- h1b
- exp
- score
- review
- app_status
- deadline
- last_seen

Filters:

- `front`
- `h1b`
- `exp`
- `review`
- `app_status`
- company
- location
- score range
- flags

Clicking a row opens a detail panel with the locally stored JD, official link, evaluator reason, flags, latest eval, review history, notes, status, and deadline controls.

### Review

Queue for ambiguous jobs, unusual title aliases, high-score jobs with uncertainty, and policy-maker examples.

Actions:

- approve
- reject
- mark needs review
- add note
- send example to policy maker

### Applications

Application tracking board or table with:

- `not_started`
- `ready`
- `applied`
- `interview`
- `rejected`
- `offer`
- `closed`

### Policies

Shows policy version and links to the markdown policy files. V1 can edit policies directly in files.

### Run History

Shows crawler and evaluator activity:

- run time
- companies crawled
- jobs found
- jobs stored
- jobs evaluated
- errors
- policy version
- model used

## GitHub Setup

The dedicated local project directory is:

```text
/Users/yj2860/Documents/quant-job-crawler
```

The target GitHub repository should be private by default because the app may contain personal application notes and locally stored job data. The recommended repository name is:

```text
9905strange/quant-job-crawler
```

If the repository already exists, set it as the local remote:

```bash
git remote add origin https://github.com/9905strange/quant-job-crawler.git
```

If it does not exist yet, create it on GitHub first, then add the remote.

## Open Questions

- Final company seed list.
- Exact first set of ATS adapters.
- Whether policy-maker updates should be applied automatically or proposed for approval.
- Which LLM model should be used for evaluator runs.
