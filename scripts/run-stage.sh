#!/usr/bin/env bash
# Run one Pi stage of the knowledge-agent pipeline headlessly.
#
# Stages: research, synthesis, output, smoke.
#
# Required environment:
#   WORK_DIR               per-run scratch directory (issue request + artifacts)
#   REPO_ROOT              repository checkout root
#   LITELLM_BASE_URL       Cloudflare Access hostname for the LiteLLM proxy
#   LITELLM_API_KEY        dedicated LiteLLM virtual key
#   LITELLM_MODEL_LOW      cheaper model for bulk reading (repository variable;
#                          used by research and smoke)
#   LITELLM_MODEL_HIGH     stronger model for writing (repository variable;
#                          used by synthesis and output)
#   CF_ACCESS_CLIENT_ID    Cloudflare Access service token id
#   CF_ACCESS_CLIENT_SECRET Cloudflare Access service token secret
#
# The stage runs Pi with only the read and write tools: no shell, no network
# tools. Web fetching happens deterministically before Pi in the research
# stage via scripts/fetch-sources.py.
set -euo pipefail

stage="${1:-}"
case "$stage" in
  research|synthesis|output|smoke) ;;
  *) echo "run-stage: unknown stage '$stage' (expected research|synthesis|output|smoke)" >&2; exit 1 ;;
esac

: "${WORK_DIR:?run-stage: WORK_DIR must be set}"
: "${REPO_ROOT:?run-stage: REPO_ROOT must be set}"

work="$(cd "$WORK_DIR" && pwd)"
repo="$(cd "$REPO_ROOT" && pwd)"

if ! command -v pi >/dev/null 2>&1; then
  echo "run-stage: pi is not installed; install @earendil-works/pi-coding-agent first" >&2
  exit 1
fi

missing=()
for var in LITELLM_BASE_URL LITELLM_API_KEY LITELLM_MODEL_LOW LITELLM_MODEL_HIGH CF_ACCESS_CLIENT_ID CF_ACCESS_CLIENT_SECRET; do
  if [ -z "${!var:-}" ]; then missing+=("$var"); fi
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "run-stage: missing configuration: ${missing[*]}" >&2
  echo "run-stage: configure the repository secrets LITELLM_BASE_URL, LITELLM_API_KEY," \
       "CF_ACCESS_CLIENT_ID, CF_ACCESS_CLIENT_SECRET and the variables LITELLM_MODEL_LOW" \
       "(research, smoke) and LITELLM_MODEL_HIGH (synthesis, output)" \
       "(see docs/agent-pipeline.md)" >&2
  exit 1
fi

export PI_OFFLINE=1
export PI_SKIP_VERSION_CHECK=1
export PI_TELEMETRY=0

# Generate the LiteLLM provider configuration. Values with env references
# are resolved by Pi at request time; nothing is printed to the log.
base_url="${LITELLM_BASE_URL%/}"
case "$base_url" in
  */v1) ;;
  *) base_url="${base_url}/v1" ;;
esac
config_dir="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
mkdir -p "$config_dir"
  LITELLM_BASE_URL="$base_url" python3 - "$config_dir/models.json" <<'PYEOF'
import json
import os
import sys


def model_entry(model_id):
    return {
        "id": model_id,
        "name": f"LiteLLM {model_id}",
        "reasoning": False,
        "input": ["text"],
        "contextWindow": 128000,
        "maxTokens": 8192,
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
    }


low = os.environ["LITELLM_MODEL_LOW"]
high = os.environ["LITELLM_MODEL_HIGH"]
config = {
    "providers": {
        "litellm": {
            "baseUrl": os.environ["LITELLM_BASE_URL"],
            "api": "openai-completions",
            "apiKey": "$LITELLM_API_KEY",
            "headers": {
                "CF-Access-Client-Id": "$CF_ACCESS_CLIENT_ID",
                "CF-Access-Client-Secret": "$CF_ACCESS_CLIENT_SECRET",
            },
            "compat": {"supportsDeveloperRole": False, "supportsReasoningEffort": False},
            "models": [model_entry(high), model_entry(low)],
        }
    },
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(config, handle, indent=2)
PYEOF

# Stage model selection: bulk reading on the low model, writing on the high model.
case "$stage" in
  research|smoke) model_id="$LITELLM_MODEL_LOW" ;;
  *) model_id="$LITELLM_MODEL_HIGH" ;;
esac

prompt_file="$work/prompt-$stage.md"

case "$stage" in
  research)
    python3 "$repo/scripts/fetch-sources.py" --request "$work/request.json" --out-dir "$work"
    {
      cat "$repo/.agents/prompts/research.md"
      printf '\n\n## Run context\n\n'
      printf 'Current UTC time: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      printf 'Repository root: %s\nScratch directory: %s (all outputs go here)\n' "$repo" "$work"
      printf 'Request: %s\nFetch report: %s\nCorpus directory: %s\n' \
        "$work/request.json" "$work/fetch-report.json" "$work/corpus"
      printf 'Repository policy: %s, %s, %s\n' \
        "$repo/AGENTS.md" "$repo/docs/okf.md" "$repo/docs/publication-policy.md"
      printf '\nWrite exactly one output file: %s\n' "$work/research.md"
    } > "$prompt_file"
    system_prompt="You are the research stage of a deterministic knowledge pipeline. Follow the stage contract exactly; the dossier file is the only deliverable."
    ;;
  synthesis)
    {
      cat "$repo/.agents/prompts/synthesis.md"
      printf '\n\n## Run context\n\n'
      printf 'Current UTC time: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      printf 'Repository root: %s\nScratch directory: %s (all outputs go here)\n' "$repo" "$work"
      printf 'Request: %s\nResearch dossier: %s\nFetch report: %s\n' \
        "$work/request.json" "$work/research.md" "$work/fetch-report.json"
      printf 'Templates: %s, %s, %s\n' \
        "$repo/templates/source-record.md" "$repo/templates/wiki-page.md" "$repo/templates/output.md"
      printf 'Repository policy: %s, %s, %s\nExisting summaries directory: %s\n' \
        "$repo/AGENTS.md" "$repo/docs/okf.md" "$repo/docs/publication-policy.md" "$repo/docs"
      printf '\nWrite outputs only under: %s\n' "$work/staged"
    } > "$prompt_file"
    system_prompt="You are the synthesis stage of a deterministic knowledge pipeline. Follow the stage contract exactly; the draft metadata file and staged concept files are the only deliverables."
    ;;
  output)
    {
      cat "$repo/.agents/prompts/output.md"
      printf '\n\n## Run context\n\n'
      printf 'Current UTC time: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      printf 'Repository root: %s\nScratch directory: %s (all outputs go here)\n' "$repo" "$work"
      printf 'Request: %s\nDraft metadata: %s\nStaged files: %s\n' \
        "$work/request.json" "$work/draft.json" "$work/staged"
      printf 'Repository policy: %s, %s\n' "$repo/AGENTS.md" "$repo/docs/publication-policy.md"
      printf '\nWrite exactly one output file under: %s\n' "$work/staged/outputs"
    } > "$prompt_file"
    system_prompt="You are the output stage of a deterministic knowledge pipeline. Follow the stage contract exactly; the requested artifact is the only deliverable."
    ;;
  smoke)
    printf 'Reply with exactly the single word: ok\n' > "$prompt_file"
    system_prompt="You are a connectivity check. Reply with one word."
    ;;
esac

cd "$work"
if [ "$stage" = "smoke" ]; then
  # Check both tiers: low (research/smoke path) then high (synthesis/output path).
  for model_id in "$LITELLM_MODEL_LOW" "$LITELLM_MODEL_HIGH"; do
    echo "run-stage: smoke check model $model_id"
    pi --print --mode text --no-session --no-extensions --no-skills \
       --no-prompt-templates --no-themes --no-context-files --no-approve --offline \
       --no-tools \
       --provider litellm --model "$model_id" \
       --append-system-prompt "$system_prompt" \
       "@$prompt_file"
  done
  echo "run-stage: smoke check completed"
  exit 0
fi

pi --print --mode text --no-session --no-extensions --no-skills \
   --no-prompt-templates --no-themes --no-context-files --no-approve --offline \
   --provider litellm --model "$model_id" \
   --tools read,write \
   --append-system-prompt "$system_prompt" \
   "@$prompt_file"

# Deterministic post-checks per stage.
case "$stage" in
  research)
    [ -s "$work/research.md" ] || { echo "run-stage: research.md was not written" >&2; exit 1; }
    ;;
  synthesis|output)
    python3 - "$work" "$stage" <<'PYEOF'
import json
import sys
from pathlib import Path

work = Path(sys.argv[1])
stage = sys.argv[2]
draft_path = work / "draft.json"
if stage == "synthesis":
    if not draft_path.is_file():
        sys.exit("run-stage: draft.json was not written")
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    mode = draft.get("mode")
    if mode == "clarification":
        question = (draft.get("clarification") or {}).get("question", "").strip()
        if not question:
            sys.exit("run-stage: clarification mode without a question")
        (work / "clarification.json").write_text(
            json.dumps({"version": 1, "question": question}, indent=2) + "\n", encoding="utf-8"
        )
    elif mode != "draft":
        sys.exit(f"run-stage: draft.json has invalid mode {mode!r}")
else:
    request = json.loads((work / "request.json").read_text(encoding="utf-8"))
    if draft_path.is_file():
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        if draft.get("mode") == "clarification":
            question = (draft.get("clarification") or {}).get("question", "").strip()
            if question:
                (work / "clarification.json").write_text(
                    json.dumps({"version": 1, "question": question}, indent=2) + "\n",
                    encoding="utf-8",
                )
                sys.exit(0)
    filename = request["deliverables"]["output"]["filename"]
    expected = work / "staged" / "outputs" / filename
    if not expected.is_file():
        sys.exit(f"run-stage: expected output artifact missing: staged/outputs/{filename}")
PYEOF
    ;;
esac

echo "run-stage: $stage stage completed"
