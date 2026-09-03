# Open Knowledge Library

A public reference library for papers, projects, and durable syntheses, maintained as an [OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md) bundle whose root is this repository.

## Contents

- [Source records](sources/) - provenance records for requested sources and issues.
- [Knowledge summaries](docs/) - question-first syntheses and repository documentation.
- [Concepts](concepts/) - atomic, reusable claims that accumulate evidence across sources.
- [Update log](log.md) - history of library changes.

## How entries are added

- Open a knowledge request issue using the *Knowledge entry* issue form and apply the `knowledge:ready` label; see [Agent pipeline](docs/agent-pipeline.md).
- Or capture manually with the templates in `templates/` and open a pull request.
