---
name: lhcb-software-environment
description: Select, construct, and verify a current LHCb Run 3 released or development software environment. Use for lb-run, lbexec, lb-dev, platform selection, DaVinci version selection, CVMFS availability, or diagnosing an LHCb application environment. Do not use for generic Python environments or legacy Run 1/2 setup unless the user explicitly requests legacy support.
license: MIT
metadata:
  era: run3
  maintainer: LHCb Agent Marketplace contributors
  last_verified: "2026-07-02"
  origin: original
  sources: "https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/davinci/; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/lhcb-dev/"
---

# LHCb software environment

Select an exact application release and compatible platform from authoritative
sample metadata.

## Workflow

1. Confirm this is a Run 3 task. Do not translate Run 1/2 commands silently.
2. Record the application, exact version, platform, data/MC status, processing
   stage, and geometry or conditions requirements. Never use `latest` in a
   reproducible command.
3. Use a released environment for normal execution:

   ```bash
   lb-run [-c <platform>] <Application>/<version> <command>
   ```

   Use `lb-dev` and the project `./run` wrapper only when modifying packages.
4. If CVMFS is mounted but `lb-run` is not already on `PATH`, initialize the
   environment with `source /cvmfs/lhcb.cern.ch/lib/LbEnv.sh`.
5. List releases with `lb-run --list <Application>` and choose one documented
   for the sample.
6. Generate the command with `scripts/check_environment.py`; use `--probe`
   only on a compatible host.
7. Pass the selected environment to `$davinci-run3`.

## Validation

- Confirm `lb-run` and `lbexec` resolve in the selected release.
- Run `lbexec --help` or a job `--dry-run`.
- Record the exact version, platform, and command.

## Failure handling

- If the environment cannot run, provide the exact command and mark execution
  unverified.
- If the sample metadata is incomplete, request it rather than inventing
  conditions, geometry, processing stage, or polarity.
- Do not use private paths, credentials, containers, or site-specific mounts
  without authorization.

## Provenance and scope

Original community guidance based on the public Run 3 Starterkit. It is not
official LHCb approval and does not cover legacy setup by default.

Sources:

- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/davinci/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/lhcb-dev/
