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

Connect the objective to exact inputs, software, outputs, validation, and open
decisions.

## Workflow

1. State the Run 3 objective, observables, and intended result.
2. Use `$lhcb-data-discovery` for each data, signal-simulation, background,
   calibration, or control input.
3. Use `$lhcb-software-environment`, `$davinci-run3`, and `$funtuple` to pin
   software, selections, variables, and output contracts.
4. Use `$analysis-productions` for scalable ntuple production and preservation.
5. Adapt `assets/analysis-spec.example.yaml`. Add collaboration requirements
   only with an authoritative source.
6. Run:

   ```bash
   python scripts/validate_spec.py analysis-spec.yaml
   ```

7. Assign or resolve every blocking decision before marking the specification
   execution-ready.

## Validation

- Require exact datasets, releases, platform, entrypoint, selection, output
  tree and branches, validation criteria, and preservation details.
- Record unresolved choices with an owner and impact.
- Source every external requirement.
- Verify executable artifacts with their owning skills; this validator does
  not establish physics correctness.

## Failure handling

- Mark inaccessible sources unverified.
- Split incompatible datasets into explicit workstreams.
- Report blocking decisions instead of choosing defaults.
- Keep unsourced policy as an open decision, not a requirement.
- Use direct public sources when optional MCPs or CDS search are unavailable.

## Provenance and scope

Original community template based on public LHCb analysis-flow, Starterkit,
and Analysis Productions material. It does not grant physics or collaboration
approval.

Sources:

- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-flow/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/
- https://lhcb.github.io/starterkit-lessons/first-analysis-steps/analysisflow.html
