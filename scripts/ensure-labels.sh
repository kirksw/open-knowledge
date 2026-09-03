#!/usr/bin/env bash
# Idempotently create the knowledge workflow labels.
# Run once locally or from a trusted environment with a repo-admin token:
#   gh auth login
#   ./scripts/ensure-labels.sh
set -euo pipefail

repo="${1:-}"
gh_args=()
if [ -n "$repo" ]; then gh_args+=(--repo "$repo"); fi

declare -a names=(
  "knowledge:ready|5A8F29|Explicit owner permission to process a knowledge issue"
  "agent:working|D4C5F9|An accepted agent run is active; prevents duplicate processing"
  "agent:needs-info|FBCA04|The agent asked a blocking clarification question"
  "agent:pr-open|0C7EBE|A reviewable pull request has been created"
  "agent:failed|B60205|A recoverable infrastructure or validation failure needs attention"
)

# Some gh versions lack `gh label view`; detect existence from a single list call.
existing="$(gh label list "${gh_args[@]}" --limit 200 --json name --jq '.[].name')"

for entry in "${names[@]}"; do
  name="${entry%%|*}"
  rest="${entry#*|}"
  color="${rest%%|*}"
  desc="${rest#*|}"
  if grep -Fxq "$name" <<<"$existing"; then
    gh label edit "$name" "${gh_args[@]}" --color "$color" --description "$desc"
  else
    gh label create "$name" "${gh_args[@]}" --color "$color" --description "$desc"
  fi
done

echo "labels ensured"
