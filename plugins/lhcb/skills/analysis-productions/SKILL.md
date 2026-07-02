---
name: analysis-productions
description: Create, review, render, validate, and locally test modern LHCb Run 3 Analysis Productions using info.yaml, lbexec entrypoints, Bookkeeping inputs, and lb-ap. Use for production job matrices, data or MC input queries, application versions, output registration, local tests, and preservation handoffs. Do not use for direct grid submission, Run 1/2 gaudirun.py productions, dataset discovery alone, or inventing working-group policy.
license: MIT
metadata:
  era: run3
  maintainer: LHCb Agent Marketplace contributors
  last_verified: "2026-07-02"
  origin: original
  sources: "https://lhcb-ap.docs.cern.ch/user_guide/creating.html; https://lhcb-ap.docs.cern.ch/user_guide/testing.html; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/"
---

# Analysis Productions

Build a reviewable Run 3 production from an already verified dataset and
DaVinci entrypoint. Keep sample-specific input under each job and share only
genuinely common settings through `defaults`.

## Workflow

1. Use `$lhcb-data-discovery` to record the exact Bookkeeping query, data/MC
   status, campaign, polarity, stream, processing stage, and conditions.
2. Use `$davinci-run3` and `$funtuple` to validate the entrypoint and expected
   ROOT artifact before production packaging.
3. Start from `assets/starterkit/info.yaml` and
   `assets/starterkit/production_job.py`. Replace the public Starterkit sample
   as one coherent unit; never mix its query, stream, process, or conditions
   with another sample.
4. Pin `application` to an exact release. Use an `application@platform` value
   when the sample needs a non-default platform.
5. Put the `lbexec` `module:function` entrypoint and common application options
   under `defaults.options`. Replace the `cernusername` contact placeholder and
   put each exact `bk_query` under its job.
6. Validate in increasing-cost order:

   ```bash
   python scripts/validate_production.py <production-directory>
   lb-ap test <production-name> <job-name> --dry-run
   lb-ap test <production-name> <job-name> -n <small-event-count>
   ```

   Older `lb-ap` releases expose separate `render` and `validate` commands;
   use them when `lb-ap --help` lists them.

7. Inspect the test log and output ROOT trees. A successful render or zero exit
   without the expected tree and entries is not sufficient.
8. Preserve the exact repository revision, rendered job, application release,
   input query, test result, output contract, and any authorized submission
   review. Do not submit or push unless the user explicitly asks.

## Production contract

- Use the Run 3 `options` mapping with `entrypoint` and `extra_options`.
- Use one exact Bookkeeping query or an upstream production job per input.
- Represent data/MC, campaign, polarity, stream, and processing differences as
  distinct jobs when their options differ.
- Do not hand-copy LFNs into `info.yaml` when a stable Bookkeeping query is
  available.
- Treat `inform`, working-group ownership, labels, retention, blinding, and
  approval rules as collaboration decisions. Include them only when the user
  supplies a current authoritative source.
- Keep optional CERN GitLab discovery read-only. If the CERN code MCP is
  absent, use the public documentation and repository web interface.

## Validation

- Run the portable validator before `lb-ap`.
- Inspect `lb-ap --help`. On `lb-ap 0.10.2`, use `lb-ap test ... --dry-run`
  for combined validation and rendering; on releases that list separate
  `render` and `validate` commands, run both.
- Initialize an LHCb proxy and CERN sign-in only when an authorized local test
  requires them.
- Verify the test output using the artifact contract from `$funtuple`.
- Record warnings as well as failures; do not reinterpret a warning without
  checking the current Analysis Productions documentation.

## Failure handling

- If `lb-ap` or CVMFS is unavailable, finish portable validation and leave
  render/validate/test evidence open.
- If Bookkeeping returns no files, return to the recorded query and campaign;
  do not broaden it silently.
- If render and runtime configurations differ, preserve the rendered
  configuration and resolve the difference before submission.
- If optional MCP integrations or CDS search are unavailable, use the public
  Analysis Productions documentation, Bookkeeping browser, and repository
  interface. CDS is never a required production step.
- Reject legacy `gaudirun.py` production defaults unless the user explicitly
  requests a Run 1/2 workflow.

## Provenance and scope

This is original community guidance based on public Analysis Productions and
Run 3 Starterkit documentation. It prepares and validates production artifacts
but does not authorize submission or define collaboration policy.

Sources:

- https://lhcb-ap.docs.cern.ch/user_guide/creating.html
- https://lhcb-ap.docs.cern.ch/user_guide/testing.html
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/
