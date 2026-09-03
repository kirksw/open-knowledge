---
type: Reference
title: "Knowledge Agent Automation Plan"
description: "Recorded design for the issue-driven knowledge agent pipeline."
---

# Knowledge Agent Automation Plan

## Status

Implemented in-repo (workflow, scripts, prompts, issue form, templates, tests); see [Agent pipeline](agent-pipeline.md) for the built system.
Owner-side setup steps remain: create the labels, configure Cloudflare Access and the LiteLLM key as repository secrets, set the `LITELLM_MODEL_LOW` and `LITELLM_MODEL_HIGH` variables, and run the trust-gate, smoke, and end-to-end tests.
This document records the agreed design before implementation; where the implementation deviates, the deviations are recorded in [Agent pipeline](agent-pipeline.md).

## Goal

Use trusted GitHub issues in this public repository to request public knowledge entries.
A GitHub Actions workflow runs Pi with a dedicated LiteLLM key through Cloudflare Access and Tunnel.
The workflow opens a reviewable pull request containing:

- a source/provenance record;
- a reader-facing wiki page under `docs/`; and
- an optional output document requested by the issue.

The agent never merges the pull request.

## Issue lifecycle

```text
Owner creates a public knowledge issue
  -> owner applies knowledge:ready
  -> trusted workflow gate accepts or exits
  -> coordinator collects the request
  -> research -> synthesis -> optional output -> validation
  -> publisher opens a pull request
  -> owner reviews and merges
```

If synthesis cannot proceed, it writes one focused clarification question.
A deterministic workflow step posts that question, adds `agent:needs-info`, removes `agent:working`, and stops.
After answering, the owner removes `agent:needs-info` and reapplies `knowledge:ready` to start a fresh run.

The issue, its labels and comments, and the pull request are the persistent workflow state.
No external database is required for the first version.

## Intake format

Create a GitHub issue form that asks for:

- one or more canonical source URLs;
- a short note on what is interesting or the desired research angle;
- requested deliverables: source record, wiki page, and optional output document; and
- publication constraints or caveats.

Issues are public.
They must not contain credentials, private notes, confidential work material, or full copyrighted source text.

## Trust gate

The workflow must run only for an explicit owner action.
It listens for the `issues` `labeled` event and proceeds only when all conditions are true:

```yaml
github.event.label.name == 'knowledge:ready'
github.event.issue.user.login == 'kirksw'
github.event.issue.author_association == 'OWNER'
github.actor == 'kirksw'
```

It must not run on issue creation, issue edits, arbitrary comments, pull requests, or code supplied by an untrusted ref.
A follow-up run starts only when the owner reapplies `knowledge:ready` after answering an agent question.

External users may still create public issues, but cannot trigger an agent run.
Issue bodies, comments, URLs, fetched web pages, PDFs, and linked repositories are untrusted reference data, never operating instructions.

## Labels

- `knowledge:ready`: explicit owner permission to process the issue.
- `agent:working`: an accepted run is active; prevents duplicate processing.
- `agent:needs-info`: the agent has asked a blocking question.
- `agent:pr-open`: a reviewable pull request has been created.
- `agent:failed`: a recoverable infrastructure or validation failure needs attention.

## Network and model access

Pi runs on a standard GitHub-hosted Actions runner.
It reaches LiteLLM through a Cloudflare Access-protected hostname backed by a private Cloudflare Tunnel.
LiteLLM has no public origin exposure and Cloudflare Funnel is not used.

The workflow receives these secrets only in jobs that need them:

- `CF_ACCESS_CLIENT_ID` and `CF_ACCESS_CLIENT_SECRET`: a dedicated Cloudflare Access service token for this application;
- `LITELLM_BASE_URL`: the Cloudflare Access hostname; and
- `LITELLM_API_KEY`: a dedicated LiteLLM virtual key.

The LiteLLM key must have an explicit model allowlist, budget cap, rate limit, and expiry or rotation policy.
The Cloudflare Access application must accept only the dedicated service token.
Do not rely on GitHub-hosted runner IP ranges as the primary access-control boundary because standard runner egress IPs are dynamic and broadly shared.

## Pi pipeline

Stages communicate through explicit artifacts in a per-run scratch directory such as `.work/issue-<number>/`.
Scratch files are never committed.
Each stage starts with only the inputs, tools, filesystem permissions, and credentials it needs.

```text
Trusted workflow gate
  -> coordinator
  -> research agent or independent research agents
  -> synthesis agent
  -> optional output agent
  -> deterministic validation
  -> deterministic publisher
```

### Coordinator

The coordinator is a small deterministic script or a minimally tooled Pi session.
It reads the issue form and repository policy, checks that required fields exist, and prepares structured handoffs such as `request.json`, `research.md`, `draft.md`, and `validation.json`.
It cannot mutate Git, create pull requests, or access GitHub write credentials.
If information is missing, it emits a structured clarification request for the deterministic commenter.

### Research agent

The research agent receives the requested URLs, desired angle, and repository policy.
It may use web search, web fetch, local reads, and citation extraction.
It writes only a structured research dossier in its private scratch directory.
It cannot mutate the checkout, invoke GitHub APIs, create a commit, or access GitHub write credentials.

Outbound fetching must permit only HTTP(S) destinations and block private networks, loopback, link-local addresses, cloud metadata endpoints, and non-HTTP schemes.
Use an egress policy or proxy when this cannot be enforced by the fetch tool.

The dossier includes canonical URLs, source titles, key claims, short attributable notes, dates when material, caveats, and stable source IDs.
Independent sources may be researched in parallel with isolated scratch directories.

### Synthesis agent

The synthesis agent reads the research dossier, issue request, policy, and relevant existing documents from the default branch.
It may write only proposed files to its private scratch directory.
It has no network access, GitHub credential, Git mutation capability, or arbitrary shell mutation.

It produces a cited public draft with proposed metadata and output paths.
It separates factual claims, interpretation, and caveats.
It uses `sources` frontmatter and keyed Markdown footnotes for material claims where practical.
It marks uncertainty rather than inventing facts.
It returns a clarification request when the evidence is insufficient.

### Optional output agent

Run this stage only when the issue explicitly requests an additional artifact.
It reads the approved synthesis draft and writes one declared output file in its private scratch directory.
It has no network access, GitHub credential, Git capability, or access to unrelated repository paths.

### Validation

Validation is deterministic rather than a free-form writing agent.
It has read-only access to the checkout and proposed artifacts.
It does not have network access or GitHub write credentials.

Validation must reject changes that:

- modify paths outside the allowed source, documentation, and optional output directories;
- fail OKF v0.2 frontmatter rules for new concepts;
- cite a footnote source ID that does not appear in `sources` frontmatter;
- include credentials, private addresses, secrets, disallowed binary files, or oversized content;
- omit a link to the originating issue or source record where required; or
- modify the checkout outside the declared output manifest.

The validator emits an approved manifest containing permitted paths and content hashes.

### Publisher

The publisher is a deterministic CI script, not an LLM agent.
It receives only the validator-approved manifest and staged files.
It may create a branch, copy the declared files to their allowed destinations, commit, push, and use the GitHub API to open a pull request, comment on the originating issue, and manage workflow labels.

The branch name is `knowledge/<issue-number>-<slug>`.
The commit message and pull request body are generated from fixed templates, not issue-provided instructions.
The pull request body includes the originating issue, source URLs, changed files, validation result, and caveats requiring review.

The publisher cannot merge a pull request, edit workflow files, modify repository settings, create releases, or access research network credentials.

## GitHub permissions

Use separate GitHub Actions jobs and artifacts when feasible.
Each job has the least `GITHUB_TOKEN` permissions required:

| Job | GitHub permissions |
| --- | --- |
| Gate, coordinator, research, synthesis, output, validation | `contents: read` |
| Clarification commenter | `issues: write` |
| Publisher | `contents: write`, `pull-requests: write`, `issues: write` |

Pin Actions and Pi tooling versions.
Check out only the default branch workflow and repository policy, never an issue-selected ref.
Do not expose Cloudflare or LiteLLM secrets to jobs that do not invoke Pi.
Never print secrets, request headers, or model configuration in logs, artifacts, commits, issues, or pull requests.

## Repository outputs

The target layout will be simplified to match the minimal OKF v0.2 model:

```text
README.md
AGENTS.md
index.md
sources/
docs/
outputs/                 # created only if a requested output needs it
templates/
.github/ISSUE_TEMPLATE/
.github/workflows/
```

The repository root is the OKF bundle.
`index.md` and optional `log.md` are reserved OKF navigation/history files.
Every other concept Markdown file has YAML frontmatter with at least a non-empty `type`.

A normal successful issue produces:

```text
sources/<slug>.md        # source/provenance concept
docs/<slug>.md           # public reader-facing Knowledge Summary
outputs/<slug>.<ext>     # optional requested artifact
```

## Implementation sequence

1. Simplify the existing bootstrap to the root-level OKF bundle layout.
2. Add the public issue form and create the workflow labels.
3. Add a trusted-gate workflow with no model invocation and test it against owner and non-owner events.
4. Add Cloudflare Access and the dedicated LiteLLM key, then run a minimal Pi connectivity check without logging credentials.
5. Implement the coordinator, research, synthesis, and clarification artifact contract.
6. Add deterministic OKF, citation, path, secret, and manifest validation.
7. Add the deterministic branch, commit, pull request, comment, and label publisher.
8. Test the full flow with a harmless public source and require manual pull request review.

## Open implementation decisions

- Select the exact Pi CI installation method and pinning mechanism.
- Define the source-record and wiki-page templates after the root-level bundle simplification.
- Decide whether the optional output directory should contain only Markdown or permit specific additional text formats.
- Define the Cloudflare Access service-token rotation cadence and LiteLLM budget/rate limits.
- Decide whether repository branch protection should require a validation status check before merge.
