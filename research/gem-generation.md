# Gem generation research

**Last updated:** 2026-10-29  
**Primary artifact:** Bejeweled Blitz Android APK version `2.29.0.29`, SHA-256 `1b9c3c6b9eb25a3de568802b5242f838e7618425c70b09c4a7fac00408a8f8b4`.  
**Artifact facts:** [APK inventory](apk-2.29.0.29-inventory.md)

## Research question

**When a gem disappears and the board refills, how does the game choose the replacement gem?** In particular, is selection independent of the board state, constrained by candidates, or adjusted for other gameplay factors?

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

## UNVERIFIED PRIOR REPORT: Disassembly interpretations from earlier discussion

A previous exploratory analysis described these addresses and interpretations, but **the instruction-level traces have not been independently reproduced in the present research record**:

| Reported ARM64 address | Earlier interpretation | Verification required |
|---|---|---|
| `0x885EB0` | `RandomGemPicker` obtains a random float, indexes candidate arrays, and references row/column logging | Confirm executable mapping, boundaries, disassembly, caller/callee targets, and data representation |
| `0x85AB94` | `RandomColor` draws an index into a configured integer list | Confirm function identity, input list, RNG call, and return value |
| `0x888374` | `GemPickerManager` chooses picker implementations according to a mode | Confirm construction branches, mode values, and use sites |
| `0x8609A4` | Spawn-related routine randomizes candidate order and tries options | Confirm function identity, candidate types, fallback behavior, and links to board refill |

These addresses must not be treated as known facts about game behavior until a reproducible assembly listing or decompiler trace accompanies them. Check that the address convention is the same as the ELF's virtual address mapping before following them.

## INFERRED: Working hypotheses to test

1. Multiple picker types **may** reflect distinct game modes, scripted setups, or test/replay configurations.
2. Candidate lists **may** limit which gem colors can be selected for a particular refill position.
3. The `REPLAY` log strings **may** support deterministic playback or diagnosis of random decisions.

These are research leads, not conclusions.

## OPEN: What remains unanswered

- Which picker runs during a normal 60-second Blitz game?
- What constructs each candidate list, and when?
- Does the selected gem depend on neighboring gems, current moves, score, elapsed time, or boosts?
- How is the random-number stream seeded or advanced?
- Is the refill distribution uniform over its candidates?
- Can a controlled replay reproduce the same board and cascades?

## Next reproducible experiment

1. Open the ARM64 library in Ghidra, record image base and analysis settings.
2. Locate cross-references to the exact `REPLAY : RandomGemPicker rowId :` and `REPLAY : SpawnGems optionIndex` strings.
3. Identify the containing functions with boundaries and instruction excerpts (small original annotations rather than large copied code blocks).
4. Map callers and callees up to board refill; distinguish replay/test-only routes from normal gameplay.
5. For each conditional branch, identify its inputs, tracked state, and outputs.
6. Write a pseudocode model only after these steps, marking every uncertainty.
7. If permitted and practical, compare predicted outcomes against controlled observation in an unmodified local game session, without accessing or interfering with live service internals.

## Rules for updating this page

Upgrade **UNVERIFIED** or **INFERRED** claims only when the new evidence is reproducible and tied to the exact artifact. Record the tool, binary architecture, native address, byte range or function name, and why the interpretation follows. Leave contradictory findings visible with an explanation of what changed.
