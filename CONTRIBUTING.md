# Contributing

This is a community project, not official LHCb guidance. Open an issue before
substantial work and keep pull requests focused.

## Contribution requirements

A proposal must identify:

- the user task, plugin, and supported era;
- authoritative public sources;
- prerequisites, credentials, filesystem access, and side effects;
- expected artifacts and a verification plan;
- a maintenance owner and workflow reviewer;
- upstream content and licensing when adaptation is proposed.

Do not submit private documentation, internal analysis material, credentials,
tokens, user-specific paths, or examples containing restricted data.

Original contributions are MIT licensed. Adapted content retains its upstream
license and must record the repository, immutable commit, original path,
license, modifications, and local maintainer. External MCP packages are
dependencies and are not relicensed by this repository.

## Development

```bash
uv sync --python 3.12 --all-groups
uv run python scripts/build_mcp_configs.py
uv run python scripts/build_adapters.py
uv run python scripts/build_catalog.py
uv run python scripts/check_all.py
```

Do not edit generated `.mcp.json`, client adapter manifests, or the catalog
block in `README.md` directly.

LHCb skill changes additionally require:

- Agent Skills and repository metadata validation;
- at least three positive and three negative routing cases;
- explicit rejection of incorrect legacy defaults;
- portable artifact checks;
- CERN-compatible execution or named manual evidence;
- approval from the relevant reviewer below.

Passing portable checks is not a substitute for CERN-runtime evidence.

## Governance and review

Repository maintainers own architecture, releases, security, client support,
and integration maintenance. Workflow reviewers own technical currency for
their area. Release approval cannot substitute for missing workflow review.

Every LHCb skill needs a named reviewer, authoritative sources, routing and
artifact evidence, and a `last_verified` date. Current LHCb guidance becomes
stale after six months unless an upstream change requires earlier review.

| Review area | Skills | Reviewer | Status |
| --- | --- | --- | --- |
| Software environment and DaVinci/FunTuple | `lhcb-software-environment`, `davinci-run3`, `funtuple` | Unassigned | Blocked |
| Analysis Productions | `analysis-productions` | Unassigned | Blocked |
| Bookkeeping/LHCbDIRAC and data discovery | `lhcb-data-discovery` | Unassigned | Blocked |
| Analysis planning methodology | `lhcb-analysis-spec` | Unassigned | Blocked |

To record acceptance, replace `Unassigned` with the reviewer’s name and stable
account, link the issue or pull request containing their evidence, update
`CODEOWNERS`, and mark the row accepted. Review does not imply official LHCb
endorsement.

Changes to plugin boundaries, supported clients, community/official status,
canonical skill format, licensing, write-capable integrations, shared MCP
services, or release-gate waivers require explicit maintainer approval and a
documented rationale in the pull request.

## Conduct

Participation must remain professional and technically constructive. Critique
claims and evidence rather than people; respect confidentiality, authorship,
licenses, identities, and institutional boundaries. Harassment,
discrimination, threats, publication of private information, deliberate
misrepresentation, retaliation, and repeated disruption are unacceptable.

Report conduct concerns privately to maintainers. Do not open a public issue
when doing so would expose a reporter, affected person, or confidential
information.

## Pull requests

State:

- scope and user-visible effect;
- validation and reviewer evidence;
- access and security implications;
- provenance and license impact;
- remaining limitations.

Use a short imperative commit summary. Maintainers may disable unsafe, stale,
or unmaintained content while it is reviewed.
