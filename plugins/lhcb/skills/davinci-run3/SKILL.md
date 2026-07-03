---
name: davinci-run3
description: Create, review, run, and troubleshoot modern LHCb Run 3 DaVinci jobs using an options function, YAML data options, PyConf, and lbexec. Use for minimal DaVinci configurations, input-process and conditions setup, line filters, dry runs, and job artifact checks. Do not use for Run 1/2 gaudirun.py or configurable-style jobs, FunTuple variable design alone, data discovery, or grid production submission.
license: MIT
metadata:
  era: run3
  maintainer: LHCb Agent Marketplace contributors
  last_verified: "2026-07-02"
  origin: original
  sources: "https://lhcb-davinci.docs.cern.ch/guide/running.html; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/minimal-dv-job/"
---

# DaVinci Run 3

Build a modern two-file job: a Python configuration function plus YAML data
options.

## Workflow

1. Use `$lhcb-software-environment` to select the release and platform.
2. Collect input files, data/MC status, processing stage, event limit, stream,
   and authoritative conditions metadata. Do not infer tags from filenames.
3. Start from `assets/print_decay_tree.py` and
   `assets/options.example.yaml`.
4. Keep the line filter, TES path, input process, stream, and sample metadata
   consistent.
5. Validate and run:

   ```bash
   python scripts/validate_job.py module.py options.yaml
   lb-run DaVinci/<version> lbexec --dry-run module:main options.yaml
   lb-run DaVinci/<version> lbexec module:main options.yaml
   ```

   Add `-c <platform>` when required. The included sample uses DaVinci `v65r0`
   with `x86_64_v3-el9-gcc13+detdesc-opt+g`.
6. Confirm the event loop, filter, TES input, and expected artifact.
7. Use `$funtuple` for ntuple configuration or ROOT verification.

## Validation

- Require `Options`, `make_config`, PyConf data handles, and `lbexec`.
- Reject `DaVinci()`, `UserAlgorithms`, `TupleFile`, and default `gaudirun.py`
  patterns for new Run 3 work.
- Record the command, release, input identity, exit status, and artifact.

## Failure handling

- If runtime tools are unavailable, report static validation only.
- For zero events, check line, process, stream, TES path, and input before
  changing analysis logic.
- For geometry or conditions failures, return to authoritative sample metadata.

## Provenance and scope

Original community templates based on public DaVinci and Run 3 Starterkit
interfaces. Review them against the selected release.

Sources:

- https://lhcb-davinci.docs.cern.ch/guide/running.html
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/minimal-dv-job/
