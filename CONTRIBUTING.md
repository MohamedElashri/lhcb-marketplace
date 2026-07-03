# Contributing

This is a community project, not official LHCb guidance. Keep changes focused
and open an issue before substantial work.

## Requirements

Describe:

- the user task, plugin, and supported era;
- authoritative public sources;
- prerequisites, credentials, filesystem access, and side effects;
- expected artifacts and validation;
- the maintainer and workflow reviewer;
- provenance and licensing for adapted content.

Do not include credentials, private documentation, restricted data, internal
analysis material, or user-specific paths. Original work is MIT licensed.
Adapted content must preserve its upstream license and immutable provenance.

## Development

```bash
uv sync --python 3.12 --all-groups
uv run python scripts/check_all.py
```

Use the relevant `scripts/build_*.py` command before the gate. Do not edit
generated MCP configs, client manifests, or the README catalog directly.

Skill changes require current public sources, positive and negative routing
coverage, legacy-default rejection, artifact validation, CERN-runtime or named
manual evidence, and reviewer approval. Changes to routing descriptions must
also meet the recorded client-routing threshold.

## Review

Maintainers own releases, security, client support, and integrations. Workflow
reviewers own technical currency. Guidance is reviewed at least every six
months or sooner after an upstream change.

All six current skills are reviewed by Mohamed Elashri
([@MohamedElashri](https://github.com/MohamedElashri), `melashri`,
`mohamed.elashri@cern.ch`) as of 2026-07-02. Review does not imply official
LHCb endorsement.

Changes to plugin boundaries, supported clients, official status, canonical
skill format, licensing, write access, shared services, or release-gate
waivers require maintainer approval.

## Pull requests

State the user-visible effect, validation, access or security impact,
provenance, reviewer, and remaining limitations. Use a short imperative commit
summary.

## Conduct

Be professional and respect confidentiality, authorship, licenses, and
identity. Harassment, discrimination, threats, disclosure of private
information, deliberate misrepresentation, retaliation, and repeated
disruption are unacceptable. Report security or conduct concerns privately
when public disclosure could cause harm.
