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

## Current status

**Verified:** The Android APK contains native ARM64 and ARM32 `libBejBlitz.so` libraries. The ARM64 binary contains strings indicating multiple gem-picker, random-number, and gameplay-related components.

**Not established:** Whether the game adjusts ordinary refill probabilities based on board state, the player's score, or difficulty; the exact algorithms for random gem selection, spawning, cascades, and scoring.

## Next experiment

Trace from a real board refill / spawn call to the candidate supply and selection logic in the ARM64 native library. Capture reproducible disassembly and call-site evidence before upgrading any behavioral explanation to VERIFIED.

---

This is an independent educational reverse-engineering project, not an official Electronic Arts or PopCap source.