# Gem generation research

**Last updated:** 2026-11-01
**Primary artifact:** Bejeweled Blitz Android APK version `2.29.0.29`, SHA-256 `1b9c3c6b9eb25a3de568802b5242f838e7618425c70b09c4a7fac00408a8f8b4`.  
**Artifact facts:** [APK inventory](apk-2.29.0.29-inventory.md)

## Research question

**When a gem disappears and the board refills, how does the game choose the replacement gem?** In particular, is selection independent of the board state, constrained by candidates, or adjusted for other gameplay factors?

## Experiment 02 result: 2026-11-01

See the [full native analysis report](experiment-02-native-gem-generation.md), [annotated evidence](evidence/experiment-02-arm64.json), and [read-only verifier](../scripts/verify_experiment_02.py).

- **VERIFIED:** All four prior addresses are function starts in the hash-identified ARM64 library. The prior string evidence is now supplemented by FDE ranges, relocation-backed vtables, caller/callee traces, and selected instructions.
- **VERIFIED:** `RandomGemPicker` selects an existing board gem using coordinates enabled by configured strings. Its demonstrated consumer is `FinisherStateController`; it must not be assumed to choose replacement colors.
- **VERIFIED:** Refill orchestration `0x8606f0` reaches compaction `0x85a710`, SpawnGems `0x8609a4`, replacement creation `0x85a408`, bulk color assignment `0x85a938`, and `Board::RandomColor` `0x85ab94`. Color candidates come from a palette copied from the active configuration.
- **VERIFIED:** The random wrapper scales a float and floors it to select a palette index. In the single-new-gem case, spawn tries shuffled palette colors against the current board. A bulk branch redraws colors until validation succeeds; another flag can bypass redraw. Validation optionally rejects matches and requires an available move.
- **INFERRED:** Conditional acceptance affects the resulting distribution. Full-span repeated swaps do not justify assuming a uniform permutation. The finisher's `count-1` and `+1` index arithmetic also needs careful modeling.
- **OPEN:** Runtime branch frequency during ordinary 60-second Blitz, complete match/move rules, exact probabilities and endpoints, active palette overrides, external seed origin, and score/time/boost dependence elsewhere.

The evidence is static. APK verification passed **320 checks**; extracted-ELF verification passed **319**. No native code or game service was executed or accessed. The next recommended work is **Experiment 03: Refill Context and Board Validation**, as specified in the full report.

## VERIFIED: Binary evidence

Inspection of `lib/arm64-v8a/libBejBlitz.so` independently confirmed literal strings associated with:

- `RandomGemPicker`
- `PatternGemPicker`
- `GemPickerManager`
- `BlitzRNGManager`
- `MersenneTwister`
- `ParkMillerLCG`
- `REPLAY : RandomColor :`
- `REPLAY : SpawnGems optionIndex`
- `REPLAY : RandomGemPicker columnId :`
- `REPLAY : RandomGemPicker rowId :`

The names offer concrete targets for disassembly. They do **not** demonstrate the runtime behavior of the picker or the probability distribution.

## Historical UNVERIFIED PRIOR REPORT: Disassembly interpretations from earlier discussion

A previous exploratory analysis described these addresses and interpretations. At the 2026-10-29 baseline, **the instruction-level traces had not been independently reproduced**. The historical table is retained below; Experiment 02 now verifies the addresses and resolves/corrects their interpretation as described above and in its address-verification table:

| Reported ARM64 address | Earlier interpretation | Verification required |
|---|---|---|
| `0x885EB0` | `RandomGemPicker` obtains a random float, indexes candidate arrays, and references row/column logging | Confirm executable mapping, boundaries, disassembly, caller/callee targets, and data representation |
| `0x85AB94` | `RandomColor` draws an index into a configured integer list | Confirm function identity, input list, RNG call, and return value |
| `0x888374` | `GemPickerManager` chooses picker implementations according to a mode | Confirm construction branches, mode values, and use sites |
| `0x8609A4` | Spawn-related routine randomizes candidate order and tries options | Confirm function identity, candidate types, fallback behavior, and links to board refill |

The original caution still applies to any other build or runtime claim. Experiment 02 supplies the missing exact-build static evidence; it does not establish that every path runs in ordinary play.

## INFERRED: Original working hypotheses (2026-10-29)

1. Multiple picker types **may** reflect distinct game modes, scripted setups, or test/replay configurations.
2. Candidate lists **may** limit which gem colors can be selected for a particular refill position.
3. The `REPLAY` log strings **may** support deterministic playback or diagnosis of random decisions.

These were research leads, not conclusions. Experiment 02 establishes a finisher configuration consumer and a separate replacement-color palette/validation path. Runtime mode selection and replay behavior remain open.

## OPEN: Runtime and broader questions

- Which picker runs during a normal 60-second Blitz game?
- Which configuration overrides construct the active session palette and finisher coordinate grids, and when are changes propagated?
- How frequently does the verified board-validation dependency affect ordinary replacements? Do score, elapsed time, or boosts affect other selection paths?
- How is the random-number stream seeded or advanced?
- Is the refill distribution uniform over its candidates?
- Can a controlled replay reproduce the same board and cascades?

## Historical next-experiment plan (2026-10-29)

Steps 1–6 below motivated Experiment 02 and have now been addressed with a comparable Capstone/ELF workflow. Step 7 was **not performed** and is outside this session's prohibition on APK/native execution. The current next experiment is the static/modeling plan in the Experiment 02 report.

1. Open the ARM64 library in Ghidra, record image base and analysis settings.
2. Locate cross-references to the exact `REPLAY : RandomGemPicker rowId :` and `REPLAY : SpawnGems optionIndex` strings.
3. Identify the containing functions with boundaries and instruction excerpts (small original annotations rather than large copied code blocks).
4. Map callers and callees up to board refill; distinguish replay/test-only routes from normal gameplay.
5. For each conditional branch, identify its inputs, tracked state, and outputs.
6. Write a pseudocode model only after these steps, marking every uncertainty.
7. If permitted and practical, compare predicted outcomes against controlled observation in an unmodified local game session, without accessing or interfering with live service internals.

## Rules for updating this page

Upgrade **UNVERIFIED** or **INFERRED** claims only when the new evidence is reproducible and tied to the exact artifact. Record the tool, binary architecture, native address, byte range or function name, and why the interpretation follows. Leave contradictory findings visible with an explanation of what changed.
