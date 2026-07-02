---
name: lhcb-data-discovery
description: Find, compare, record, and validate LHCb Run 3 data or simulation datasets using Bookkeeping, LHCbDIRAC, processing metadata, LFNs, and access checks. Use for event types, campaigns, magnet polarity, streams, HLT2 or Sprucing outputs, file manifests, and dataset provenance. Do not use for generic web search, physics-literature discovery, direct production submission, or choosing undocumented sample metadata.
license: MIT
metadata:
  era: run3
  maintainer: LHCb Agent Marketplace contributors
  last_verified: "2026-07-02"
  origin: original
  sources: "https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/bookkeeping/; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/files-from-grid/; https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/"
---

# LHCb data discovery

Turn a physics data requirement into an exact, reviewable Bookkeeping selection.
Do not construct a plausible path from memory and present it as discovered.

## Workflow

1. Record the era, data or simulation, year, processing stage, desired stream
   or line, polarity coverage, and purpose.
2. For simulation, also record the event type, beam/simulation conditions,
   generator, pile-up, simulation campaign, and whether the sample is flagged
   or filtered.
3. Search the Bookkeeping browser. Compare complete paths and file metadata;
   do not select solely because a campaign name sorts newest.
4. Record the chosen query with `assets/dataset-record.example.yaml`. Keep
   unresolved fields explicit rather than guessing them.
5. Validate the record:

   ```bash
   python scripts/validate_dataset_record.py dataset-record.yaml
   ```

6. With an authorized proxy, obtain LFNs or test one replica:

   ```bash
   lhcb-proxy-init
   lb-dirac dirac-dms-get-file LFN:/lhcb/...
   ```

   Prefer a generated catalog or remote read when downloading large files is
   unnecessary.
7. Pass the exact record to `$analysis-productions`,
   `$lhcb-software-environment`, and `$davinci-run3`.

## Discovery contract

- Data: record year, processing campaign, polarity, stream, file type, data
  quality choice where applicable, and complete Bookkeeping query.
- Simulation: additionally record event type, generator/configuration,
  simulated conditions, campaign, and flagging/filtering semantics.
- Runtime: record the input process, application release/platform decision,
  and geometry/conditions metadata from authoritative sample sources.
- Provenance: record the source URL or interface, verification date, selection
  rationale, and alternatives rejected.
- Access: separate dataset existence from replica accessibility. A valid path
  can still require a proxy or have unavailable replicas.

Optional CERN GitLab or research MCPs may help locate public production code or
papers, but they are not authoritative for Bookkeeping contents. If absent,
use the Bookkeeping browser and public documentation. CDS record search is
currently degraded and must not be required.

## Validation

- Confirm every selected record has a complete Bookkeeping query.
- Confirm data/MC status agrees with the query and runtime `simulation` flag.
- Confirm polarity, campaign, stream, file type, and input process are mutually
  consistent.
- For a runnable handoff, verify at least one LFN or replica with authorized
  access and record the result without storing credentials.

## Failure handling

- If Bookkeeping or LHCbDIRAC access is unavailable, return the search contract
  and mark the query unverified; do not fabricate results.
- If candidate datasets differ in campaign or processing, preserve the
  alternatives and request physics/working-group guidance.
- If no simulation exists for a required polarity or campaign, record the gap
  instead of silently substituting another sample.
- If replica access fails, refresh the catalog or proxy before changing the
  dataset selection.
- Reject Run 1/2 Stripping or Turbo assumptions as Run 3 defaults.

## Provenance and scope

This is original community guidance derived from public Run 3 Starterkit
Bookkeeping and file-access workflows. It records selection evidence but does
not replace Bookkeeping, LHCbDIRAC, or working-group review.

Sources:

- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/bookkeeping/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/files-from-grid/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/
