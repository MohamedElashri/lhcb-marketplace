---
name: lhcb-analysis-spec
description: Create, review, and validate auditable LHCb Run 3 analysis specifications spanning physics objectives, datasets, software, selections, outputs, validation, provenance, open decisions, and preservation. Use for measurement plans, efficiency studies, control studies, analysis handoffs, and readiness reviews. Do not use to invent collaboration policy, approve physics choices, discover datasets by itself, or replace executable DaVinci and production validation.
license: MIT
metadata:
  era: run3
  maintainer: LHCb Agent Marketplace contributors
  last_verified: "2026-07-02"
  origin: original
  sources: "https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-flow/; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/; https://lhcb.github.io/starterkit-lessons/first-analysis-steps/analysisflow.html"
---

# LHCb analysis specification

Create a decision ledger that connects the physics objective to exact inputs,
software, outputs, validation, and preserved evidence. An explicit open
decision is preferable to a plausible invented value.

## Workflow

1. State the objective, supported Run 3 use case, observables, and intended
   result without asserting approval.
2. Use `$lhcb-data-discovery` for each data, signal-simulation, background,
   calibration, or control input. Record missing samples as open decisions.
3. Use `$lhcb-software-environment`, `$davinci-run3`, and `$funtuple` to pin
   executable software, selections, fields, variables, and output contracts.
4. Use `$analysis-productions` for scalable ntuple production and preservation.
5. Start from `assets/analysis-spec.example.yaml`. Keep sample metadata and
   collaboration requirements out of defaults; add them only with a cited
   source.
6. Validate:

   ```bash
   python scripts/validate_spec.py analysis-spec.yaml
   ```

7. Resolve or explicitly assign every blocking decision before calling the
   specification execution-ready.

## Specification contract

- `analysis`: stable identifier, Run 3 era, use case, objective, and status.
- `physics`: decay or sample definition, observables, and requested outputs.
- `datasets`: role, data/MC kind, exact query, campaign, polarity, process, and
  provenance for every input.
- `software`: exact application version, platform, entrypoint, and environment
  source.
- `selection`: persisted line/TES relationship and stream.
- `outputs`: file, tree, minimum entries, and required branches.
- `validation`: static, runtime, artifact, and comparison checks with pass
  criteria.
- `decisions`: stable IDs, owners, status, evidence, and impact.
- `preservation`: code revision, environment, data identity, and result
  location strategy.
- `external_requirements`: only user-supplied collaboration policy with a
  public or authorized source. An empty list means no policy was asserted.

Representative use cases include a signal measurement, a simulation
efficiency study, and a control/validation study. They can share structure but
must not silently share dataset or physics assumptions.

Optional research MCPs can help locate literature and public HEPData records.
If absent, use direct public sources. CDS search is degraded and must not be a
required evidence path.

## Validation

- Require exact releases and dataset queries; reject `latest` and placeholders.
- Require at least one dataset, output tree, branch, validation check, and
  preservation record.
- Require unresolved dataset or physics choices to have an open decision.
- Verify executable artifacts with the owning skills; this validator checks
  the specification contract, not physics correctness.
- Confirm every external policy requirement includes its source.

## Failure handling

- If a source is inaccessible, retain the claim as unverified or remove it.
- If datasets disagree in campaign, polarity, or processing, split the
  workstreams and record the comparison.
- If an open decision blocks execution, report it rather than choosing a
  convenient default.
- If a requested policy has no authoritative source, place it in an open
  decision and do not encode it as a requirement.
- Reject Run 1/2 tools and workflows as implicit Run 3 defaults.

## Provenance and scope

This original community template is based on public LHCb analysis-flow,
Starterkit, and Analysis Productions material. It improves auditability but
does not constitute physics, working-group, or collaboration approval.

Sources:

- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-flow/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/
- https://lhcb.github.io/starterkit-lessons/first-analysis-steps/analysisflow.html
