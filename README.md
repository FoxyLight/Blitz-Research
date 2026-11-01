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

## Current status

**VERIFIED (static, exact build):** Experiment 02 independently verified all four previously reported addresses and traced board compaction, replacement creation, palette-based color draws, and board validation. `RandomGemPicker` has a finisher consumer that selects existing gems; the replacement-color path uses `Board::RandomColor`. A single-new-gem branch tries palette colors until a board check passes; a bulk branch can redraw colors until validation succeeds.

**OPEN:** Which branches and configurations run during ordinary timed play, exact probabilities and float endpoints, seed origin, palette overrides, and any score/time/difficulty dependence elsewhere. Static board-validation dependence is established; its runtime frequency and complete rule semantics are not.

**Reproduction:** Capstone 5.0.7 and pyelftools 0.33, with exact APK/ELF SHA-256 gates. The APK run passed 320 checks; ELF-only input passed 319. See Experiment 02 for commands, annotated pseudocode, and limits. No game code was executed and no proprietary binaries are included.

## Next experiment

**Experiment 03: Refill Context and Board Validation.** Trace refill flags from cascade callers, reconstruct match/move acceptance rules, and build an independent model with hand-authored board fixtures. Trace palette overrides and seed propagation while keeping the APK/native code unexecuted. See the [Experiment 02 recommendation](research/experiment-02-native-gem-generation.md#recommended-experiment-03-refill-context-and-board-validation).

---

This is an independent educational reverse-engineering project, not an official Electronic Arts or PopCap source.
