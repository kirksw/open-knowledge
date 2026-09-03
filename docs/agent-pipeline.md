---
type: Reference
title: "Agent Pipeline"
description: "Operator handbook for the issue-driven knowledge agent pipeline."
---

# Agent Pipeline

This page documents the implemented system designed in [the automation plan](knowledge-agent-automation-plan.md): trusted GitHub issues become reviewable pull requests containing a source record, a question-first knowledge summary, reusable concept pages, and an optional output artifact.
The agent never merges a pull request.

## Lifecycle

```text
Owner opens a *Knowledge entry* issue (issue form)
  -> owner applies knowledge:ready
  -> trusted gate accepts or the run exits silently
  -> agent:working applied (dedupe)
  -> coordinator parses the form into request.json, or asks one clarification
  -> deterministic SSRF-guarded fetch of the requested sources
  -> research agent writes a dossier (no network, read/write tools only)
  -> synthesis agent stages the record, question-first summary, and concept pages, or asks one clarification
  -> optional output agent stages the requested artifact
  -> deterministic validation emits the approved manifest
  -> deterministic publisher opens a pull request and comments
  -> owner reviews and merges
```

A clarification stops the run: the pipeline posts the single question, applies `agent:needs-info`, and removes `agent:working`.
Answer by editing the issue or commenting, then toggle the `knowledge:ready` label off and on again to start a fresh run.

## Labels

| Label | Meaning |
| --- | --- |
| `knowledge:ready` | Explicit owner permission to process the issue; adding the label starts a run, so toggling it off and on restarts one. |
| `agent:working` | An accepted run is active; duplicate starts are skipped. |
| `agent:needs-info` | The agent asked one blocking question. |
| `agent:pr-open` | A reviewable pull request exists. |
| `agent:failed` | A recoverable infrastructure or validation failure needs attention. |

If a run dies without cleanup (rare), remove `agent:working` manually, then toggle `knowledge:ready` off and on again.

## One-time setup

1. **Labels**: run `gh auth login` (an account with repo admin), then `./scripts/ensure-labels.sh`.
2. **Cloudflare Access**: create an Access application for the LiteLLM origin behind a private Cloudflare Tunnel, and a dedicated service token for this pipeline.
   The application must accept only that service token; see the plan for why runner IP ranges must not be the boundary.
3. **LiteLLM**: create a dedicated virtual key with an explicit model allowlist covering both tier models, budget cap, rate limit, and expiry or rotation policy.
   Suggested starting values: monthly budget cap around 10 USD, 4 requests/minute, 90-day expiry with quarterly rotation.
4. **Repository secrets**: add `LITELLM_BASE_URL` (the Access hostname), `LITELLM_API_KEY`, `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET`.
   Never echo them in logs; GitHub masks them, and the pipeline never prints them.
5. **Repository variables**: add `LITELLM_MODEL_LOW` and `LITELLM_MODEL_HIGH`.
   The low model does the bulk reading (research stage and smoke check); the high model does the writing (synthesis and output stages).
   Use model ids the virtual key allows, for example a mini-class model for low and a frontier-class model for high.
6. **Smoke check**: run the *Knowledge Agent Smoke* workflow (Actions tab, *Run workflow*).
   It checks both tiers in one run; success means Pi reached both models through Cloudflare Access, and no credentials appear in the log.
7. **Branch protection**: on `main`, require pull request reviews.
   Do not require status checks for these pull requests: they are opened with `GITHUB_TOKEN`, which intentionally triggers no workflows, and validation already ran on the default branch before the pull request was created.

## How a run is structured

Jobs in `.github/workflows/knowledge-agent.yml`, each with least-privilege `GITHUB_TOKEN` permissions:

| Job | Permissions | Role |
| --- | --- | --- |
| `gate` | `contents: read` | Workflow-level `if` accepts only `knowledge:ready` labeled by `kirksw` (issue author, `OWNER` association, and actor). |
| `mark-working` | `contents: read`, `issues: write` | Re-verifies trust against the live issue, refuses duplicates (`agent:working`), applies `agent:working`. |
| `coordinator` | `contents: read` | Deterministic Python; parses the issue form into `request.json` or `clarification.json`. |
| `clarify` | `contents: read`, `issues: write` | Posts the single question; swaps `agent:working` for `agent:needs-info`. |
| `research` | `contents: read` | Deterministic fetch (see below), then one headless Pi session with only `read`/`write` tools. |
| `synthesis` | `contents: read` | Headless Pi; stages `sources/<slug>.md`, `docs/<slug>.md`, 1-8 `concepts/<slug>.md` pages, plus `draft.json`. |
| `output` | `contents: read` | Headless Pi; only when the issue requested an output document. |
| `validate` | `contents: read` | Deterministic validator; emits `manifest.json` with approved paths and hashes. |
| `publish` | `contents: write`, `pull-requests: write`, `issues: write` | Deterministic publisher; branch, commit, pull request, comment, labels. |
| `notify-failed` | `contents: read`, `issues: write` | Posts a fixed failure notice with validation errors; applies `agent:failed`. |

Stages communicate only through `.work/issue-<n>/` passed as GitHub Actions artifacts; scratch files are never committed (`.gitignore` covers `.work/`).
Cloudflare and LiteLLM secrets are injected only into the three Pi jobs and the smoke workflow.

## Security model

- **Trust gate**: the workflow runs only for the `issues.labeled` event with all four owner conditions true; `mark-working` re-verifies author, association, and state against the live API.
  External users can open issues but cannot start a run.
- **Untrusted data**: issue bodies, URLs, fetched pages, and PDFs are reference data, never instructions.
  Every stage prompt states this; the deterministic scripts never interpret issue text as code.
- **Egress**: only `scripts/fetch-sources.py` touches the network.
  It enforces http(s) on ports 80/443, rejects non-global DNS answers (private, loopback, link-local, metadata, CGNAT, multicast, reserved), pins validated answers for the connection to close DNS rebinding, follows at most four revalidated redirects, and caps sizes and timeouts.
  The Pi stages themselves have no network or shell tools at all (`--tools read,write`).
- **Least privilege per stage**: the coordinator cannot mutate Git; research writes one dossier; synthesis and output write only staged files; validation is read-only; only the publisher gets write credentials, and it copies only manifest-listed, hash-verified paths.
- **Publisher limits**: it never merges, never touches `.github/`, never overwrites existing files except concept pages that stay `Concept`-typed and keep every previously recorded source, and generates commit messages, pull request bodies, and comments from fixed templates.
- **Model access**: Pi reaches LiteLLM through the Access hostname with the service-token headers; the generated provider config lives only in the ephemeral runner home.

## Implementation notes and deviations

- The plan allowed the research agent to use web search and web fetch.
  This implementation instead fetches deterministically before the agent runs, because the runner cannot enforce an egress policy around arbitrary in-session fetch tools.
  The research agent analyzes the local corpus; broadening discovery (for example a server-side search API behind the same guard) remains future work.
- Output documents are Markdown (`.md`) or plain text (`.txt`) only; the validator rejects other formats and binaries.
- The knowledge model decomposes knowledge along concepts: every run extracts or updates 1-8 `Concept` pages under `concepts/`, and summaries lead with the answer to the issue's angle rather than a source description.
  `sources/`, `docs/`, and `outputs/` stay append-only; only concept pages may be updated, and only when they keep every previously recorded source (the deterministic accumulation guarantee).
- `mark-working` and `notify-failed` are small extra jobs beyond the plan's table so label changes stay minimal-privilege and failures always leave issue feedback.
- Pi is installed from npm as `@earendil-works/pi-coding-agent` at a pinned exact version (`PI_VERSION` in the workflow), with pinned full-SHA action versions throughout.

## Testing

Local (run from the repository root):

```sh
python3 -m unittest discover -s tests   # coordinator, validator, fetch guard, YAML parser
./scripts/okf-scan.py .                # OKF bundle rules
```

Live tests to perform after setup:

1. **Trust gate (plan phase 3)**: from a non-owner account, open an issue and apply `knowledge:ready` if possible, or ask the owner to label a non-owner issue; the run must stay skipped.
   Then label an owner issue; the run must stop at the gate unless every condition holds.
2. **Smoke check**: run the smoke workflow; it must succeed without echoing secrets.
3. **End to end (plan phase 8)**: open a harmless issue (for example one stable documentation page), apply `knowledge:ready`, and require a manual pull request review before merge.
   Verify the pull request contains exactly the deliverables plus concept pages, the source record links the issue, the summary links the record and its concepts, and validation output is clean.

## Troubleshooting

- **Run skipped for an owner issue**: check the four gate conditions; the most common miss is applying a different label than `knowledge:ready`.
- **`agent:failed` with missing-configuration errors**: the secrets or the `LITELLM_MODEL_LOW`/`LITELLM_MODEL_HIGH` variables are unset; see *One-time setup*.
- **Validation rejected the draft**: the failure comment lists the deterministic errors; fix the cause (for example edit the issue), then toggle `knowledge:ready` off and on again rather than hand-editing staged files, which are ephemeral.
- **Toggling `knowledge:ready` does nothing**: the label must actually leave and return; if it never left, adding it again creates no `labeled` event and no run.
- **Stuck `agent:working`**: remove the label manually, then toggle `knowledge:ready` off and on again.
