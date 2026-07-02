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

Select an explicit application version and platform before generating or
running an LHCb workflow. Treat the input sample metadata as authoritative.

## Workflow

1. Establish the era. Default to Run 3 only when the request or input metadata
   supports it. If the task is Run 1/2, stop and request an explicitly legacy
   workflow; do not translate old commands silently.
2. Determine whether the user needs a released environment or a source
   development build:
   - Use `lb-run` for a released application.
   - Use `lb-dev`, a checkout, and the project `./run` wrapper only when code
     changes or a development build are required.
3. Record the application, exact version, platform, data/MC status, processing
   stage, and geometry/conditions requirements. Never substitute `latest` for
   an exact version in a reproducible command.
4. If CVMFS is mounted but `lb-run` is not already on `PATH`, initialize the
   standard environment with
   `source /cvmfs/lhcb.cern.ch/lib/LbEnv.sh`.
5. Discover available releases with `lb-run --list <Application>`. Select the
   newest release that is documented as suitable for the sample, not simply
   the numerically newest release.
6. Generate and inspect the command with
   `scripts/check_environment.py`. Add `--probe` only on a CERN-compatible
   host.
7. Pass the recorded environment contract to `$davinci-run3` or the next
   application-specific skill.

## Environment selection details

Use a released environment for normal execution:

```bash
lb-run [-c <platform>] <Application>/<version> <command>
```

Use a development build only when modifying packages:

```bash
lb-dev --name <directory> <Application>/<version>
cd <directory>
git lb-use <project>
git lb-checkout <revision> <package>
make
./run <command>
```

The checkout revision, package, platform, and geometry technology depend on the
sample and task. Public examples are evidence for their samples, not universal
defaults.

## Validation

- Confirm `lb-run` and `lbexec` are available through the selected release.
- Run `lbexec --help` or the target job with `--dry-run` before processing
  events.
- Record the resolved application version and platform in the result.
- For a development build, build successfully and use `./run`, not a released
  `lb-run` environment accidentally.

## Failure handling

- If CVMFS is mounted but `lb-run` is unavailable, source the standard
  `LbEnv.sh` first. If either remains unavailable, provide the exact command
  and state that execution remains unverified.
- If the sample metadata is incomplete, request it rather than inventing
  conditions tags, geometry, processing stage, or polarity.
- If the selected release lacks a compatible platform, inspect available
  platforms and use `-c best` only as an explicit, recorded fallback.
- Do not use containers, private paths, credentials, or site-specific mounts
  without user authorization.

## Provenance and scope

This is original community guidance derived from the public Run 3 Starterkit.
It is not official LHCb approval. It supports Run 3; legacy setup is a
non-trigger unless explicitly requested.

Sources:

- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/davinci/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/lhcb-dev/
