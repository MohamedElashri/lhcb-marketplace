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

Build a reviewable production from a verified dataset and DaVinci entrypoint.

## Workflow

1. Use `$lhcb-data-discovery` to record the exact Bookkeeping query, data/MC
   status, campaign, stream, processing stage, and conditions.
2. Use `$davinci-run3` and `$funtuple` to validate the entrypoint and expected
   ROOT output.
3. Start from `assets/starterkit/info.yaml` and
   `assets/starterkit/production_job.py`. Replace the sample query, stream,
   process, and conditions together.
4. Pin `application` to an exact release or `application@platform`. Put the
   `lbexec` entrypoint under `defaults.options`, replace `cernusername`, and
   keep each exact `bk_query` under its job.
5. Validate:

   ```bash
   python scripts/validate_production.py <production-directory>
   lb-ap test <production-name> <job-name> --dry-run
   lb-ap test <production-name> <job-name> -n <small-event-count>
   ```

   Use separate `render` and `validate` commands if the installed `lb-ap`
   exposes them.
6. Verify the ROOT tree and entries. Preserve the revision, rendered job,
   release, query, result, and output contract.
7. Do not submit or push without explicit authorization.

## Validation

- Use Run 3 `options` with `entrypoint` and `extra_options`.
- Use exact Bookkeeping queries and separate jobs when sample options differ.
- Include collaboration policy only when the user supplies an authoritative
  source.
- Use credentials only for an authorized local run.

## Failure handling

- If runtime tools are unavailable, report portable validation only.
- If Bookkeeping returns no files, verify the query; do not broaden it.
- Resolve rendered/runtime differences before submission.
- Use public documentation and Bookkeeping when optional MCPs or CDS search
  are unavailable.

## Provenance and scope

Original community guidance based on public Analysis Productions and Run 3
Starterkit documentation. It does not authorize submission or define policy.

Sources:

- https://lhcb-ap.docs.cern.ch/user_guide/creating.html
- https://lhcb-ap.docs.cern.ch/user_guide/testing.html
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/
