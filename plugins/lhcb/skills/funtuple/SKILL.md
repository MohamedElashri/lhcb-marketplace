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

Configure only the fields and variables required by the analysis, then verify
the produced ROOT structure rather than assuming success from a zero exit code.

## Workflow

1. Use `$davinci-run3` for the surrounding application, input, line filter, and
   YAML options.
2. Record the exact persisted decay descriptor used by the input selection.
   Define one unique field name per desired particle and place exactly one
   caret for each non-head field.
3. Build `FunctorCollection` objects from explicit ThOr functors or current
   `FunTuple.functorcollections`. Separate candidate and event variables.
4. Keep field keys synchronized with the `variables` mapping. Do not add
   speculative variables or silently translate legacy LoKi TupleTools.
5. Adapt `assets/tuple_job.py` and `assets/options.example.yaml`, then run:

   ```bash
   python scripts/validate_config.py tuple_job.py options.yaml
   lb-run DaVinci/<version> lbexec --dry-run tuple_job:main options.yaml
   lb-run DaVinci/<version> lbexec tuple_job:main options.yaml
   python scripts/verify_output.py tuple.root --tree BToDsPiTuple/DecayTree
   ```

6. Inspect the actual ROOT keys if the expected tree differs. Verify entry
   count and required branches with repeated `--branch` arguments.

## Run 3 guardrails

- Use `FunTuple_Particles`, `fields`, `variables`, `tuple_name`, and `inputs`.
- Prefer ThOr functors and current functor collections.
- Reject `DecayTreeTuple`, `TupleTool*`, `addBranches`, and default Run 1/2
  LoKi patterns unless the user explicitly requests a legacy workflow.
- Make the descriptor match the persisted input selection; a physically
  equivalent descriptor is not necessarily structurally compatible.
- Keep an event pre-filter aligned with the selected HLT2 or Spruce line.
- Treat MC truth, trigger information, isolation, and fitter outputs as
  separate, sample-dependent additions that require targeted validation.

## Output contract

Before execution, record the output filename, expected tree path, minimum
entry count, required branches, release, and sample identity. After execution,
list the actual ROOT keys and validate the tree and branches. A created file is
not sufficient evidence.

For empty output, check input access, process and stream, line and filter, TES
location, descriptor compatibility, then functor errors—in that order. Do not
weaken physics selections merely to make an artifact non-empty.

## Validation

- Run the static validator before execution and the ROOT verifier afterward.
- Treat a missing tree, zero entries, or missing branches as a failed artifact.
- Record the tuple file, tree path, entry count, required branches, DaVinci
  release, and execution command.

## Failure handling

- On zero candidates, inspect the input process, stream, line, TES location,
  filter, and descriptor before modifying cuts or functors.
- On a missing functor, check the selected DaVinci release documentation; do
  not substitute a similarly named legacy functor.

## Provenance and scope

The template and validators are original community material based on public
DaVinci and Run 3 Starterkit interfaces. Physics-variable selection remains an
analysis decision and requires review.

Sources:

- https://lhcb-davinci.docs.cern.ch/configuration/davinci_configuration.html
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/thor-functors/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/functor-collections/
