---
name: funtuple
description: Design, review, and verify modern LHCb Run 3 FunTuple configurations and ROOT ntuple outputs. Use for decay fields, caret placement, ThOr functors, FunctorCollection composition, event variables, tuple naming, branch checks, and output inspection. Do not use for legacy DecayTreeTuple or LoKi TupleTools, general DaVinci environment setup, data discovery, or physics-variable choices without user requirements.
license: MIT
metadata:
  era: run3
  maintainer: LHCb Agent Marketplace contributors
  last_verified: "2026-07-02"
  origin: original
  sources: "https://lhcb-davinci.docs.cern.ch/configuration/davinci_configuration.html; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/thor-functors/; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/functor-collections/"
---

# FunTuple

Configure only required fields and variables, then verify the ROOT output.

## Workflow

1. Use `$davinci-run3` for the application, input, filter, and YAML options.
2. Match fields to the exact persisted decay descriptor. Use one field name
   per particle and one caret for each non-head field.
3. Build `FunctorCollection` objects with current ThOr functors. Keep field
   keys synchronized with `variables` and separate event variables.
4. Adapt `assets/tuple_job.py` and `assets/options.example.yaml`, then run:

   ```bash
   python scripts/validate_config.py tuple_job.py options.yaml
   lb-run DaVinci/<version> lbexec --dry-run tuple_job:main options.yaml
   lb-run DaVinci/<version> lbexec tuple_job:main options.yaml
   python scripts/verify_output.py tuple.root \
     --tree BToDsPiTuple/DecayTree --branch B_M
   ```

   The included sample uses DaVinci `v65r0` with
   `x86_64_v3-el9-gcc13+detdesc-opt+g`.
5. Verify the expected tree, non-zero entries, and all required branches.

## Validation

- Require `FunTuple_Particles`, `fields`, `variables`, `tuple_name`, and
  `inputs`.
- Reject `DecayTreeTuple`, `TupleTool*`, and default LoKi patterns.
- Record the output file, tree, entry count, branches, release, and command.

## Failure handling

- For empty output, check access, process, stream, line, TES path, filter, and
  descriptor before changing cuts.
- For missing functors, consult the selected release documentation; do not
  substitute legacy equivalents.

## Provenance and scope

Original community templates based on public DaVinci and Run 3 Starterkit
interfaces. Physics-variable selection remains an analysis decision.

Sources:

- https://lhcb-davinci.docs.cern.ch/configuration/davinci_configuration.html
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/thor-functors/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/functor-collections/
