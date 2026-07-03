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

Turn a data requirement into an exact, reviewable Bookkeeping selection.

## Workflow

1. Record data or simulation, year, processing stage, stream or line, polarity,
   and purpose. For simulation, add event type, conditions, generator,
   campaign, and flagging or filtering.
2. Search Bookkeeping and compare complete paths and file metadata. Never
   invent a path or select only because a campaign is newest.
3. Record the chosen query with `assets/dataset-record.example.yaml`. Keep
   unresolved fields explicit rather than guessing them.
4. Validate:

   ```bash
   python scripts/validate_dataset_record.py dataset-record.yaml
   ```

5. With an authorized proxy, obtain LFNs or test one replica:

   ```bash
   lhcb-proxy-init
   lb-dirac dirac-dms-get-file LFN:/lhcb/...
   ```

6. Pass the exact record to `$analysis-productions`,
   `$lhcb-software-environment`, and `$davinci-run3`.

## Validation

- Record the complete query, data/MC kind, campaign, polarity, stream, file
  type, process, conditions, source, verification date, and rationale.
- Keep dataset existence separate from replica accessibility.
- For a runnable handoff, verify one LFN or replica without storing
  credentials.

## Failure handling

- If access is unavailable, return the search requirements and mark results
  unverified.
- Preserve conflicting alternatives and missing samples; do not substitute
  silently.
- Use Bookkeeping directly when optional MCPs or CDS search are unavailable.
- Refresh the catalog or proxy before changing a selected dataset.

## Provenance and scope

Original community guidance based on public Run 3 Starterkit workflows. It
does not replace Bookkeeping, LHCbDIRAC, or working-group review.

Sources:

- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/bookkeeping/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/files-from-grid/
- https://lhcb-starterkit-run3.docs.cern.ch/first-analysis-steps/analysis-productions/
