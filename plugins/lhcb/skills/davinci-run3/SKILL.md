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

Build a modern two-file DaVinci job: a Python configuration function and YAML
data options. Keep analysis logic separate from sample-specific metadata.

## Workflow

1. Use `$lhcb-software-environment` to record an exact DaVinci version and
   compatible platform.
2. Collect the input files, data/MC status, processing stage, event limit,
   stream where applicable, and authoritative geometry/conditions metadata.
   Do not infer tags from filenames.
3. Start from `assets/print_decay_tree.py` and
   `assets/options.example.yaml`, or review equivalent user files.
4. Replace the example line, input, processing stage, and sample metadata
   together. Ensure the TES path and line filter refer to the same line.
5. Run:

   ```bash
   python scripts/validate_job.py module.py options.yaml
   lb-run DaVinci/<version> lbexec --dry-run module:main options.yaml
   lb-run DaVinci/<version> lbexec module:main options.yaml
   ```

   Add the verified `-c <platform>` after `lb-run` when required.
6. Confirm the event loop starts, the line filter behaves as expected, the TES
   input exists, and the requested artifact or log evidence is produced.
7. Use `$funtuple` when the task moves from job execution to ntuple fields,
   functors, or ROOT output verification.

## Run 3 guardrails

- Use `from DaVinci import Options, make_config` and return
  `make_config(options, ...)`.
- Run through `lbexec` with a Python function and YAML options.
- Prefer PyConf data handles and `create_lines_filter`.
- Reject implicit Run 1/2 defaults such as `DaVinci()`, `UserAlgorithms`,
  `TupleFile`, configurable-style global mutation, or a default
  `gaudirun.py` command.
- Treat `input_process`, simulation status, tags, input stream, and raw format
  as sample-dependent. Include only fields justified by authoritative
  metadata.
- Keep initial runs small and use `--dry-run` before event processing.

## Job contract

The Python file must expose a callable such as `main(options: Options)` and
return `make_config(options, algorithms)`. For persisted HLT2 or Spruce
selections, keep the event filter, TES location, input process, and stream
consistent.

The YAML options must decide `input_files`, `input_type`, `input_process`,
`simulation`, `evt_max`, and `print_freq`. Add an input manifest, stream, raw
format, geometry version, or conditions tags only when required by
authoritative sample metadata.

Verify in order: static validation, `lbexec --dry-run`, a small event sample,
exit status and artifact inspection, then larger-scale execution.

## Validation

- Static validation proves structure only; it does not prove that a release,
  TES location, conditions set, or remote input is valid.
- Preserve the exact command, resolved release, input identity, exit status,
  and expected artifact in the handoff.

## Failure handling

- If `lb-run` is unavailable, report the static result and leave runtime
  verification open.
- If a filter fires zero events, verify the line name, processing stage,
  stream, and input manifest before changing analysis logic.
- If conditions or geometry fail, return to sample metadata; never try random
  tags until the job starts.

## Provenance and scope

The templates and validator are original community material based on public
DaVinci and Run 3 Starterkit interfaces. They require review against the
selected release and do not constitute official LHCb guidance.

Sources:

- https://lhcb-davinci.docs.cern.ch/guide/running.html
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/minimal-dv-job/
