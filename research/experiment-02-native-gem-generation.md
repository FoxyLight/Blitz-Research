# Experiment 02: Native Gem-Generation Analysis

**Date:** 2026-11-01  
**Method:** Read-only static analysis of the user-supplied APK. No installation, execution, emulation of APK instructions, modification, security bypass, traffic capture, or game-service access.  
**Baseline read before investigation:** all repository documents at commit `a4f6d564fec533a5a824cea14a202de98b4703c1`: README, [inventory](apk-2.29.0.29-inventory.md), and [gem-generation research](gem-generation.md). Earlier interpretations were treated as hypotheses.

## Result

**VERIFIED:** All four reported addresses are ARM64 function starts in this exact library. However, they belong to two different paths. `RandomGemPicker` selects an **existing gem** from coordinates supplied through finisher configuration. The traced replacement-color path instead uses `Board::RandomColor`, a configured palette, and `BlitzLogic` spawn/validation logic.

**VERIFIED:** Board state enters the spawn decision. For exactly one newly created gem, the routine tries colors from a shuffled palette and checks the resulting board after each assignment. For multiple new gems, one branch redraws all their colors until validation succeeds. A flag can bypass that redraw. The validation routine can reject existing matches and requires an available move.

**OPEN:** This establishes static control/data flow, not the frequency of these branches in ordinary 60-second play. It does not establish adaptive difficulty, score-dependent color weighting, or an exact empirical probability distribution.

## Artifact and tool identity

| Item | Independently observed |
|---|---|
| APK | `com.ea.BejeweledBlitz.com.apk`, 126,485,803 bytes, 2,002 ZIP entries |
| Manifest | `com.ea.BejeweledBlitz_na`; version `2.29.0.29`; versionCode `995` |
| APK SHA-256 | `1b9c3c6b9eb25a3de568802b5242f838e7618425c70b09c4a7fac00408a8f8b4` |
| Selected member | `lib/arm64-v8a/libBejBlitz.so` |
| ELF size | 26,337,872 bytes |
| ELF SHA-256 | `21764c7e81d4ae5eb4f6fbc5c8acbe2eb40447bb7b345db6f0859333ef0a2b2f` |
| ELF build ID | `f03da685fe6dd40cb0f322b118225931c4407c91` |
| ELF format | AArch64, ELF64, little endian; `.dynsym`, no ordinary `.symtab` |
| Analysis tools | Capstone 5.0.7, pyelftools 0.33; Python version recorded in validation output |
| Manifest decoder | Androguard 4.1.4 `AXMLPrinter`, read-only |

Ghidra was not used. Capstone disassembly, ELF relocation analysis, RTTI/vtable reconstruction, and exception-unwind function ranges supplied the comparable static-analysis workflow. This is manually annotated pseudocode, not recovered original source or automatic decompiler output.

All addresses below are **ELF virtual addresses with load bias zero**, not live-process addresses. `.text` is `[0x797000, 0x17a2e98)`. The first executable `PT_LOAD` has file offset and virtual address zero, so code VAs here also happen to equal file offsets. That equality does **not** apply to the writable segments: use `fileOffset = p_offset + VA - p_vaddr`. Resolve `.rela.dyn` before interpreting vtable pointers.

## Evidence and address verification

The machine-readable [evidence record](evidence/experiment-02-arm64.json) contains 39 function ranges and digests, 189 selected instruction checkpoints with explanatory groups, and 31 relocation checks. The [verifier](../scripts/verify_experiment_02.py) checks exact artifact identity first, then independently decodes `.eh_frame` FDE ranges, instructions, relocation addends, and identifying literals. It can generate complete local listings for inspection without committing them.

**Observed validation:** APK input: **320/320 checks passed**. Extracted ELF input: **319/319 checks passed**; the APK hash check is unavailable for ELF-only input. These checks substantiate recorded binary facts. They are not tests of runtime branch reachability or every semantic interpretation below.

| Prior address | VERIFIED range, exclusive end | Identity evidence | Assessment of earlier interpretation |
|---|---|---|---|
| `0x885EB0` | `[0x885eb0,0x886334)` | RTTI name at `0x48ac3c`; relocation `0x17cdcd8`; primary vtable slot `0x17cdc60`; row/column log references | Float/index arithmetic confirmed, but it selects existing board coordinates, not replacement colors. |
| `0x85AB94` | `[0x85ab94,0x85ac8c)` | `Board` RTTI at `0x48a024`; slot `0x17ca3d0`; `RandomColor` reference at `0x85abfc` | Configured 32-bit palette lookup confirmed. RNG stream ID is an argument; refill callers pass `1`. |
| `0x888374` | `[0x888374,0x88844c)` | `GemPickerManager` RTTI at `0x48acd9`; slot `0x17cde80`; constructor calls | Factory branching confirmed; observed consumer is finisher configuration. |
| `0x8609A4` | `[0x8609a4,0x860bcc)` | `BlitzLogic` RTTI at `0x48a0da`; slot `0x17ca7f8`; SpawnGems log reference at `0x860a44` | Spawn/color retry logic confirmed; single-item and bulk cases differ. |

All four are exact FDE starts, not merely addresses within neighboring functions. Their FDE lengths equal the next `.eh_frame_hdr` index spacing. Constructors, RTTI, relocation-backed slots, and callers provide identity evidence beyond string proximity. Names such as `refill`, `validate`, and the flag names below are analyst labels; source-level method names were stripped.

## VERIFIED call trace to refill

The following virtual targets are resolved for objects constructed with the recorded vtables. An alternate dynamic implementation could change an indirect target; no runtime object trace was collected.

| Caller and call site | Receiver / slot | Resolved target and effect |
|---|---|---|
| `0x85f4fc`, call `0x85f7e8` | `BlitzLogic +0xf0`, arguments `1,0` | `0x8606f0`, refill orchestration |
| `0x8606f0`, call `0x860810` | `logic+0x2a0` (`Board`), slot `+0xd8` | `0x85a710`, remove marked gems and compact columns |
| `0x8606f0`, call `0x860828` | `BlitzLogic +0xf8` | `0x8609a4`, create replacements and choose colors |
| `0x8609a4`, call `0x8609ec` | `Board +0xd0` | `0x85a408`, acquire/reset gems, set row/column and insert into board |
| Bulk branch, call `0x860a9c` | `Board +0xe8` | `0x85a938`, assign a color to each new gem |
| `0x85a938`, calls `0x85a97c`, `0x85a9a8` | `Board +0x20`, stream ID `1` | `0x85ab94`, RandomColor; results stored to gem `+0x54` |
| `0x85ab94`, call `0x85abbc` | logic RNG accessor | `0x865d34` → `0x86ece0`, lookup integer-keyed RNG stream |
| `0x85ab94`, call `0x85abdc` | `BlitzRandom +0x30` | `0x8a5f88` → float-range slot `+0x20` → `0x8a5f20` |
| `0x8a5f20` → `0x8a5d94` | wrapper draw slot `+0x18`, then underlying PRNG `+0x18` | `0x83e8c8`, `MersenneTwister` state advance / float result |

`BlitzLogic` constructor `0x85bdfc` constructs a `Board` through `0x8589e4` and stores it at `+0x2a0` (`0x85c390–0x85c398`). It constructs the RNG manager at `+0x1a0` (`0x85c174–0x85c17c`). This connects the receiver fields to their implementations.

**VERIFIED additional context:** Setup function `0x85e3d4` also calls the same refill slot at `0x85e940`, with first argument zero and a second flag influenced by configuration/another component (`0x85e8c4–0x85e940`). Thus those flags must not be assumed constant across the game. `0x85f7e8` supplies a concrete `1,0` caller, but its presence alone is not a runtime observation of ordinary play.

## VERIFIED candidate-color origin and RNG operations

1. `Board` stores a vector of 32-bit color codes at `+0x70` (begin), `+0x78` (end), `+0x80` (capacity).
2. Board reset `0x858c6c` copies that vector from `logic->activeConfig` (`logic+0x288`), field `+0x1b0`, at `0x858c78–0x858c98`.
3. The single-new-gem branch copies the same Config palette to a separate `BlitzLogic` scratch vector at `+0xe8`, at `0x860a08–0x860a24`.
4. Configuration-default initializer `0x8710a0` creates a `GemColors` object, invokes its `+0x20` enumeration routine `0x8709d8`, and moves the returned integer vector to configuration field `+0x1b0` (`0x871334–0x871384`). `GemColors` constructor `0x8700e0` defines `red=1`, `orange=2`, `yellow=3`, `green=4`, `blue=5`, `purple=6`, `white=7`. Enumeration traverses its tree and appends values at `0x870ad0–0x870ad8` / `0x870b38–0x870b48`. `Config` here is a descriptive label for the active configuration structure, not a recovered source type name.

**OPEN:** Those are constructor defaults. Palette overrides, the active session's exact list/order/duplicates, and how configuration changes propagate to Board were not exhaustively traced. Do not turn the seven default codes into an asserted seven-color distribution for every mode.

`RandomColor` passes bounds `0.0f` and `float(palette.size())` to the RNG's integer-range slot. `BlitzRandom` computes a float range as `lo + (hi-lo)*u` (`0x8a5f44–0x8a5f4c`), then floors it with `fcvtms` (`0x8a5f9c`). `RandomColor` uses that signed index to load a palette code (`0x85ac60`). No neighbor lookup, score read, palette weighting, or rejection loop occurs **inside this function**. That is a local finding; its caller adds board validation.

`BlitzRNGManager` initialization `0x86e6bc` creates five separate `BlitzRandom` / `MersenneTwister` pairs keyed `1` through `5`; the constructor of each wrapper retains an underlying PRNG at `+8`. Refill draws and its shuffle use key `1`. The finisher's RandomGemPicker separately constructs its own wrapper and MT object (`0x885a38–0x885a68`) and seeds through the logic getter at slot `+0x468` (`0x885a6c–0x885a94`), whose implementation `0x8666c4` reads logic `+0x418`.

The underlying MT routine uses a 624-word state and MT-style twist/tempering. Its final observed conversion is a 31-bit value converted to binary32 and multiplied by binary32 `2^-31` (`0x83e9ec–0x83ea00`). ParkMillerLCG is present elsewhere but was not the PRNG constructed along these traced paths. Reseed routine `0x86ec30` forwards one supplied seed to the managed streams; the external origin of that seed remains **OPEN**.

**INFERRED endpoint concern:** Binary32 rounding can round a high 31-bit integer to `2^31`, making the scaled float exactly `1.0`. There is no visible clamp in the wrapper or RandomColor. This makes it unsafe to promise a strictly half-open range or exact uniformity from the formula alone. Whether a reachable session state produces the concerning endpoint, and its consequences, remain **OPEN**; no native code was run to test it.

## Annotated pseudocode: refill and replacement colors

This is a structural model of verified instructions. Vector/string notation and names are **INFERRED representations** of observed pointer triples, strides, RTTI, copies, and operations. Allocation, logging, cleanup, and unrelated event dispatch are omitted. `virtual` calls below use the constructor-established targets above.

```text
RandomColor(board, streamId):                    # 0x85ab94
    colors = board.vector_at_0x70               # 32-bit entries
    rng = lookup(board.logic.rngManager, streamId)
    index = rng.intRange(0.0f, float32(len(colors)))
    return colors[index]                       # no local bounds clamp

refill(logic, skipMatchCheck, keepBulkColors):   # 0x8606f0, analyst flag names
    if any existing gem has pending movement/status:
        return                                 # 0x8607bc–0x8607f0
    perform_pre_refill_callbacks()
    compact_columns(logic.board)               # 0x85a710
    spawn(logic, skipMatchCheck, keepBulkColors)
    perform_post_refill_callbacks()

spawn(logic, skipMatchCheck, keepBulkColors):    # 0x8609a4
    created = create_missing_top_gems(board)    # 0x85a408; installed in board
    if len(created) == 0:
        return
    if len(created) == 1:
        options = copy(logic.activeConfig.palette)
        n = len(options)
        for i in range(n):
            j = rng(stream=1).intRange(0.0f, float32(n))
            swap(options[i], options[j])        # full-span swaps, 0x860aa4
        for color in options:
            created[0].color_at_0x54 = color    # 0x860b60
            if validate(board, skipMatchCheck): # 0x860b6c
                break
        return                                 # no explicit success result;
                                               # last trial remains if all fail
    while true:                                # two or more created gems
        if not keepBulkColors:
            for gem in created:                # 0x85a938
                gem.color_at_0x54 = RandomColor(board, 1)
        if validate(board, skipMatchCheck):     # 0x860a70–0x860a84
            return
        # Actual branch returns to 0x860a88; no retry cap found here.
        # With keepBulkColors set, this loop does not redraw colors.

validate(board, skipMatchCheck):                # 0x860bd8
    if not skipMatchCheck:
        matches = collect_matches(board)       # Board +0xc8 -> 0x85a3e4
                                               # -> MatchGenerator 0x83fc0c
        count = len(matches)
        release_match_results(matches)
        if count > 0:
            return false
    moves = find_moves(board)                   # MoveFinder 0x86ef38
    count = len(moves)
    release_move_results(moves)
    return count > 0
```

**VERIFIED geometry:** The Board owns 64 gem-pointer cells at `+0xa0`. Compaction scans eight columns, moving/removing gems according to flags. Creation `0x85a408` scans each column for its first existing gem and fills rows above it, or all eight rows if empty. It acquires gems through a pool, resets them, sets row/column at `+0x58/+0x5c`, inserts them into the board, and returns a vector of new gem pointers. This is the concrete refill operation, not just a routine with a matching log name.

**VERIFIED board dependence:** `collect_matches` receives current board storage through `0x85a3e4`; `MoveFinder` scans the board in `0x86ef38` and checks neighboring positions in `0x86f08c`. Their counts control the color retry decisions. Therefore a final accepted assignment can depend on the current arrangement even though each direct `RandomColor` draw is a palette/RNG lookup. The single-gem loop tries a finite list; the bulk branch has no visible retry limit in this function. These observations do not establish a difficulty-adjustment policy.

**INFERRED distribution implications:** Full-span repeated swaps are not the usual shrinking-range Fisher–Yates procedure, so uniform permutation probabilities must not be assumed. Conditional acceptance also prevents inferring the final-board distribution solely from a uniform-draw hypothesis. No probabilities or retry frequencies were measured.

## Annotated pseudocode: RandomGemPicker and manager

**VERIFIED consumer:** `FinisherStateController` configuration `0x8852cc` creates `GemPickerManager` (`0x885320`), calls its factory at `0x8853d8`, stores the returned picker at controller `+0x20`, obtains configuration rows through slot `+0x68`, and feeds each row to the picker's `+0x10` (`0x885414–0x885444`). For RandomGemPicker this is adjustor thunk `0x885b7c` → deep-copy routine `0x885a98`. A preparation call then reaches `0x885b9c`. A picker adapter is constructed at `0x88546c`; its prefetch `0x88b004` invokes the picker's `+0x18`, which resolves through `0x886334` to `0x885eb0`.

```text
GemPickerManager.create(logic, config):         # 0x888374
    mode = config.virtual_0x58()
    if mode == 0:
        return IGemPicker_subobject(new RandomGemPicker(logic))
    if mode == 1:
        return IGemPicker_subobject(new PatternGemPicker(logic.board))
    if mode == 2:
        custom = new CustomPickerManager(logic, config.virtual_0x60())
        return custom.virtual_0x10()
    return previously_stored_picker             # invalid mode has no new factory

RandomGemPicker.prepare():                     # 0x885b9c
    eligibleRows = []
    for r, stringRow in configuredGrid:
        if any(cell != "0" for cell in stringRow):
            eligibleRows.append(r)

RandomGemPicker.pick():                        # 0x885eb0
    u = ownRng.floatRange(0.0f, 1.0f)
    k = floor_unsigned(float32(u * float32(len(eligibleRows)-1)))
    r = eligibleRows[k]                         # 0x885f20; no preceding empty guard
    eligibleColumns = [c for c in range(len(configuredGrid[r]))
                       if configuredGrid[r][c] != "0"]
    v = ownRng.floatRange(0.0f, 1.0f)
    j = float32(floor(float32(v * float32(len(eligibleColumns)-1))) + 1.0f)
    if len(eligibleColumns) != 0 and 0 <= j < len(eligibleColumns):
        return board.getGem(r, eligibleColumns[unsigned(j)])
    return null
```

`board.getGem` is `0x859eb8`, reached through Board slot `+0xa0` at `0x88614c`. It bounds-checks both coordinates to `0..7` and loads an existing pointer; it does not create a color or a gem.

**VERIFIED unusual arithmetic:** The first selection uses `count-1`; the second also uses `count-1` and then adds `1`. Do not silently replace these with a conventional `floor(u*count)`. For a hypothetical exact `u,v` in `[0,1)`, this formula omits the last eligible row index and the first eligible-column-list index; a one-element eligible-column list produces `j=1`, failing the range check. This is an arithmetic consequence, not a measured runtime bias or a confirmed defect. Configuration assumptions and reachable float endpoints remain **OPEN**.

The strings are tested against literal `"0"` at `0x432698`, not parsed as candidate color codes by this function. Their nonzero values enable coordinates; the returned object comes from the live Board. The name/log text therefore gave a misleading lead for replacement-color selection. This experiment proves a finisher consumer exists, not that it is the only consumer anywhere in the program.

## Uncertainties and boundaries

| Status | Finding / remaining question |
|---|---|
| VERIFIED | Four addresses, function ranges, RTTI/vtable identities, refill creation/color-assignment path, palette source field, range/floor wrapper, board-validation branch structure. |
| INFERRED | C++ vector/string abstractions and descriptive flag names; permutation/distribution implications conditional on the RNG model. |
| OPEN | Runtime mode and branch frequency in ordinary timed Blitz; all callers and writes of both flags; palette overrides and synchronization; initial external seed source and complete RNG consumption order. |
| OPEN | Full MatchGenerator / MoveFinder rule semantics, special-gem exceptions, exact retry termination guarantees, and invalid/empty configuration behavior. |
| OPEN | Reachable float endpoints, exact color/permutation probabilities, and whether the finisher's unusual indexing is intentional for its configurations. |
| OPEN | Score, elapsed time, boosts, or difficulty may affect other code/configuration paths; this trace neither proves nor excludes them globally. |

Replay-prefixed logs are corroborating strings. Their presence does not establish replay-only code, deterministic end-to-end playback, live log output, or a live-service mechanism. `BlitzRandom` draw forwarding was inspected; logging-related string construction does not establish that a log was emitted.

## Reproduction

Use a locally owned copy of the exact APK. No proprietary artifact is included in this repository. The verifier reads ZIP/ELF data as bytes; it never imports the `.so`, invokes Android tools, or executes APK code.

```powershell
python -m venv work/venv
work/venv/Scripts/python.exe -m pip install -r scripts/requirements-experiment-02.txt
work/venv/Scripts/python.exe scripts/verify_experiment_02.py `
  --apk 'C:/path/to/com.ea.BejeweledBlitz.com.apk' `
  --extract-dir work/input `
  --listing-dir work/listings `
  --report work/verification-apk.json
work/venv/Scripts/python.exe scripts/verify_experiment_02.py `
  --elf work/input/libBejBlitz-arm64.so `
  --report work/verification-elf.json
```

Output paths must be fresh; the script refuses overwrites. Expected results are 320 checks for the APK and 319 for the ELF. Hash mismatches fail before disassembly or extraction. These dependencies and their parsers run on the research machine; the game binaries do not run. Linux/macOS users can substitute `work/venv/bin/python` and shell line continuations.

To review the inference rather than only compare checkpoints:

1. Inspect local listings `008606f0`, `008609a4`, `0085a408`, `0085a938`, `0085ab94`, and `00860bd8` in call order.
2. Follow the relocation addends for `0x17ca7f0`, `0x17ca7f8`, `0x17ca480`, `0x17ca498`, `0x17ca3d0`, and `0x17ca800` in the evidence JSON. Confirm the receiver constructors, not just the slots.
3. Inspect `008852cc`, `00885a98`, `00885b9c`, and `00885eb0` separately. Keep configuration strings and board pointers distinct from palette color codes.
4. Follow `008a5f88`, `008a5f20`, `008a5d94`, and `0083e8c8`; preserve binary32 arithmetic and rounding in any future independent model.
5. Optionally import the extracted ELF into Ghidra as ELF/AARCH64 little endian, image base zero. Record your Ghidra version and analysis options separately. Check the FDE ranges and relocation-backed vtables above before renaming functions. No Ghidra result is claimed by this report.

The committed evidence is a small annotated selection and digests, not a dump of complete functions. Generated full listings, binaries, and extracted assets belong under ignored `work/`. Do not commit them.

## Recommended Experiment 03: Refill Context and Board Validation

Continue static analysis by tracing the two refill flags from ordinary cascade update through `0x85f4fc` and `0x8606f0`, including early returns and configuration changes. Recover the precise acceptance rules reached through `0x85a3e4` and `0x86ef38`, then write an independent small board model with hand-authored fixtures: one hole versus multiple holes, immediate-match versus no-match candidates, and zero versus positive available moves.

The deliverable should explain **which caller enables each branch and why a candidate passes**, with a caller/flag table, annotated acceptance pseudocode, and fixture predictions. Also trace palette override writes and seed propagation far enough to identify the inputs needed for reproducibility. Keep reachable endpoint analysis separate from statistical claims. Execute only the independently written model; retain the current restriction against APK/native execution and live services.
