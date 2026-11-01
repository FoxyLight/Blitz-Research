# Bejeweled Blitz Research

This repository is the **authoritative research record** for our independent study of Bejeweled Blitz's gameplay logic.

**Scope:** Understand how the game represents its board, selects new gems, detects matches, handles cascades, scores moves, and implements special gems. Research is read-only: do not alter the app or its online services. Do not commit proprietary APKs, native libraries, extracted artwork, or confidential material.

## Research discipline

Every substantive claim must be labeled as one of:

- **VERIFIED:** Directly reproduced from an identified artifact or observable behavior, with enough detail for someone else to check.
- **INFERRED:** A reasoned interpretation supported by evidence but not yet established.
- **OPEN:** A question that has not been answered.
- **UNVERIFIED PRIOR REPORT:** Described in earlier exploration but not independently reproduced in the repository evidence.

Use exact APK versions, architecture, filenames, checksums, tools, dates, native addresses where relevant, and any caveats. A class name or logging string **does not** prove that a given path runs during ordinary gameplay.

## Current source artifact

An Android APK provided for local research was independently inspected on **2026-10-29**. Its metadata and ELF inventory are documented in [research/apk-2.29.0.29-inventory.md](research/apk-2.29.0.29-inventory.md). The APK itself is **not** stored here.

## Findings and ongoing work

- [APK metadata and native-code inventory](research/apk-2.29.0.29-inventory.md)
- [Gem generation: evidence, interpretation, and open questions](research/gem-generation.md)
- [Experiment 02: Native Gem-Generation Analysis](research/experiment-02-native-gem-generation.md)
- [Experiment 02 reproducible evidence](research/evidence/experiment-02-arm64.json) and [read-only verifier](scripts/verify_experiment_02.py)
- [Experiment 03: Refill Context and Board Validation](research/experiment-03-refill-context-and-board-validation.md)
- [Experiment 03 static evidence](research/evidence/experiment-03-arm64.json), [read-only verifier](scripts/verify_experiment_03.py), and [validation record](research/evidence/experiment-03-validation.json)
- [Independent ordinary-gem model](models/refill_model.py), [original fixtures](tests/fixtures/experiment-03-boards.json), [runner](scripts/run_experiment_03_model.py), and [57-case results](research/evidence/experiment-03-model-results.json)

## Current status

**VERIFIED (static, exact build):** Experiment 02 separated existing-gem picker consumers from replacement-color selection. Experiment 03 maps the update caller's flags `(1,0)` and setup's `(0,B)`, reconstructs match/move validation, and distinguishes zero, single, and bulk replacement branches. A skips immediate-match rejection but still requires a move. B preserves colors only in the bulk color branch and also affects an orchestration callback. The single branch can return after exhausting rejected candidates; the bulk loop has no visible local retry cap.

**VERIFIED (independent model):** 57 original hand-authored cases pass, including all flag combinations and the 16 ordinary supporting-pair patterns. These are model results compared with reconstructed static rules, not observations of native execution.

**OPEN:** Runtime reachability/frequency, special-type and override semantics, external seed origin and first-draw ordering, palette-loading invariants, and termination conditions enforced outside refill. Board validation does not establish adaptive difficulty.

**Reproduction:** Capstone 5.0.7 and pyelftools 0.33 with exact APK/ELF SHA-256 gates. Experiment 03 passed 404 APK checks and 403 ELF-only checks; the Experiment 02 APK regression passed 320. Its independent model needs only Python. See the reports for commands, annotated pseudocode, and limitations. No game code was executed and no proprietary binaries are included.

## Next experiment

**Experiment 04: Refill Preconditions, Preset Palettes, and Seed Ordering.** Trace the configuration/rules and rare-object prerequisites of the identified branches, establish palette synchronization and preserved-color validity conditions, and order queued seed consumption against the first color draw. Keep the same static-only boundary. See the [Experiment 03 recommendation](research/experiment-03-refill-context-and-board-validation.md#findings-ledger-and-recommended-experiment-04).

---

This is an independent educational reverse-engineering project, not an official Electronic Arts or PopCap source.
