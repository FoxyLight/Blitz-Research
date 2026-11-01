# Experiment 03: Refill Context and Board Validation

**Date:** 2026-11-01

**Baseline:** `92505f2cd5fa16eb5fd9b90822d291829219b3b2` in the authoritative `FoxyLight/Blitz-Research` repository. All nine tracked files at that baseline, including both Experiment 02 evidence records and its verifier, were read before this investigation. Historical documents and original artifacts were preserved.

**Method:** Read-only static analysis plus an independently written board model. No APK/native execution, installation, instruction emulation, modification, security bypass, or live game-service access.

## Result and evidence boundary

**VERIFIED, static:** The update-context caller reaches `0x8606f0` with flags `(1,0)`. Setup reaches it with `(0,B)`, where B derives from an active rare-gem object and a nonempty configuration string. Refill can return early while existing gems have particular pending-state fields. Once replacement objects are created, zero, one, and multiple replacements follow different acceptance and termination rules.

**VERIFIED, static:** Flag A skips immediate-match rejection; it does **not** skip the available-move requirement. Flag B skips color reassignment in the multiple-replacement branch; it is ignored by the single-replacement branch. One replacement has a finite palette pass that can finish without acceptance. Multiple replacements have a retry back-edge with no local iteration cap. B=1 can revisit validation without changing colors in that loop body.

**VERIFIED, model execution:** All **57 original cases pass**. Two independently written ordinary-gem move calculations agree on the fixtures: geometric placement and the 16 reconstructed supporting-pair patterns. These results test our interpretation and harness, not the proprietary program.

**INFERRED:** The update-context path is a cascade/ongoing-board context, and the reset path is initial/setup context. A configuration string and rare-gem state explain some exceptional refill behavior. These descriptions follow static structure; no session establishes their runtime frequency.

**OPEN:** Full event reachability, special numeric gem-type semantics, matching-override writers, palette loading, external seed origin, seed-event timing relative to the first draw, and termination guarantees imposed outside the refill body. Board-dependent validation is not evidence of adaptive difficulty.

## Artifact, tools, and reproducible evidence

| Item | Identity / result |
|---|---|
| APK | User-supplied `com.ea.BejeweledBlitz.com.apk`, version `2.29.0.29`, versionCode `995`, package `com.ea.BejeweledBlitz_na` |
| APK SHA-256 | `1b9c3c6b9eb25a3de568802b5242f838e7618425c70b09c4a7fac00408a8f8b4` |
| ARM64 member | `lib/arm64-v8a/libBejBlitz.so`, 26,337,872 bytes |
| ELF SHA-256 | `21764c7e81d4ae5eb4f6fbc5c8acbe2eb40447bb7b345db6f0859333ef0a2b2f` |
| Build ID | `f03da685fe6dd40cb0f322b118225931c4407c91` |
| Tools used | Python 3.14.7; Capstone 5.0.7; pyelftools 0.33 |
| Baseline regression | Experiment 02 APK verifier: 320 checks passed again |
| Experiment 03 verifier | APK: 404/404 checks passed; extracted ELF: 403/403; unrelated synthetic input rejected by the hash gate |
| Experiment 03 evidence | 40 FDE function ranges/digests, 285 instruction sites, 32 relocation entries, one eight-entry jump table |
| Model | Standard-library Python; original code and hand-authored 8×8 boards; scripted random indices |

Addresses are ELF virtual addresses with load bias zero, not live addresses. Function boundaries come from `.eh_frame` FDEs. Translate VAs through the containing `PT_LOAD`; do not apply code/file-offset equality to writable segments. Relocations and constructors bind indirect calls to concrete implementations. A recorded vtable target is conditional on that receiver type, not proof that every runtime receiver has that type.

The [machine-readable evidence](evidence/experiment-03-arm64.json) groups instruction sites by claim. The [read-only verifier](../scripts/verify_experiment_03.py) independently decodes those facts after checking artifact hashes. Function digests cover the complete relevant bodies, including branches omitted from short pseudocode. The [validation record](evidence/experiment-03-validation.json) records actual check counts; [model results](evidence/experiment-03-model-results.json) include expected and actual outcomes, attempts, draws, and source hashes. Byte agreement does not automatically prove the analyst's semantic interpretation.

## Caller chain and flag origins

### VERIFIED: concrete receiver and call chain

App initialization `0xd65de8` calls singleton getter `0xd5bb84` at `0xd660b0` and stores the result at app `+0x320`. The getter calls the `BlitzLogic` constructor `0x85bdfc` at `0xd5bbe8`. App update-context routine `0xd68eb4` loads that field and dispatches slot `+0x338` at `0xd691f0`, resolving to `0x85f4fc` for this vtable. This supplies a receiver chain in addition to the prior string/vtable evidence.

```text
app update-context 0xd68eb4
  -> app.logic (+0x320), slot +0x338 -> 0x85f4fc
     -> when entry gates pass and work vector is empty:
        logic slot +0xf0, (A=1, B=0) -> 0x8606f0
          -> Board slot +0xd8 -> 0x85a710 (compaction)
          -> logic slot +0xf8 -> 0x8609a4 (replacement/color branching)
             -> Board slot +0xd0 -> 0x85a408 (replacement objects)
             -> logic slot +0x100 -> 0x860bd8 (acceptance)
```

**VERIFIED entry gates:** `0x85f4fc` returns when TimerLogic slot `+0xa0` (`0x85b55c`, byte `timer+0x65`) is true, or when logic slot `+0x208` (`0x85c960`) is true. The second gate delegates into TimerLogic and another component; its complete user-facing meaning is **OPEN**. After intervening handlers, pointers at logic `+0x3c8/+0x3d0` must compare equal at `0x85f7c4..0x85f7d0` before the `(1,0)` call at `0x85f7e8`. A nonempty work vector takes another branch. These conditions limit the static path; they do not establish which session events satisfy it.

### VERIFIED: caller/flag mapping

Names below are analyst labels. Both flags are propagated through bit zero, not interpreted as arbitrary integers.

| Caller / call site to slot `+0xf0` | A: skip immediate-match rejection | B: preserve bulk colors | Context and limits |
|---|---:|---:|---|
| `0x85f4fc` / `0x85f7e8` | 1 | 0 | Update handlers and empty work-vector gate; ongoing cascade context **INFERRED** |
| `0x85e3d4` / `0x85e940` | 0 | Conditional | Board reset/setup; initial-board interpretation **INFERRED** |
| `0x86614c` / `0x8661a0` | 1 | 0 | Requires logic byte `+0x3c !=0`; performs refill then processes a supplied string/event context; precise event names **OPEN** |
| `0x8666cc` / `0x8666ec` | 1 | 0 | Refill callback followed by another logic callback; concrete session purpose **OPEN** |

This is a mapping of demonstrated callers, not an exhaustive proof over every possible indirect dispatch or subclass.

**Setup B derivation:** `0x85e3d4` first invokes Board slot `+0x28` (`0x858c6c`) at `0x85e4fc`. Later it reads logic `+0x328`, a constructor-bound `RareGemsLogic` object, and its active object pointer at `+0x30`. If nonnull, active-object slot `+0xe8` supplies a value at `0x85e8d8`. A nonempty active-configuration string at `+0x1e0` forces B true; otherwise the rare-object result supplies B. The low bit is passed at `0x85e92c`; A is zeroed at `0x85e934`. Subsequent board-string/pattern processing supports a preset-board interpretation (**INFERRED**). The exact rare-object override implementations and all string producers remain **OPEN**.

**Orchestrator deferral:** Before compaction/spawn, `0x8606f0` visits existing gems. It returns if gem slot `+0x68` yields a positive float, or slot `+0x58` yields true. The concrete Gem implementations are `0x84100c` (float `gem+0x1c`) and `0x840ffc` (byte `gem+0x17`). Animation/pending-state meaning is **INFERRED**; the raw predicates are **VERIFIED**. A and B are masked at `0x860818/0x86081c` and forwarded by `0x860828`. B also skips a post-spawn branch at `0x86082c`; it must not be treated as solely a global color-generation switch. That downstream branch is outside the minimal model.

## Validation algorithm

### VERIFIED: board acceptance, `0x860bd8`

1. With A=0, invoke Board slot `+0xc8` -> `0x85a3e4`. Capture the match-result count, return results to the pool, and reject a positive count. The move finder is not called on this rejection.
2. With A=1, skip that match test.
3. Obtain Board's move finder at `+0x90`, invoke its slot `+0x30` -> `0x86ef38`, capture the result count before pool release, and accept only a positive count.

```python
# Original annotated reconstruction; not native source.
def accept(board, A):                       # 0x860bd8
    if not (A & 1):                        # 0x860bec
        matches = board.detect_matches()   # +0xc8 -> 0x85a3e4
        n = count(matches)
        release_to_pool(matches)
        if n > 0:                          # 0x860c20..0x860c34
            return False
    moves = board.move_finder.find()        # +0x30 -> 0x86ef38
    n = count(moves)
    release_to_pool(moves)
    return n > 0                           # 0x860c78..0x860c7c
```

### VERIFIED: match scanning, `0x85a3e4` -> `0x83fc0c`

Board forwards its cell-pointer vector at `+0xa0` and an integer override vector at `+0x58`. Override accessor `0x840974` returns zero for an invalid/out-of-range index; a nonzero entry substitutes for `gem+0x54` as the effective match color. This is distinct from the palette used to draw replacements. Writers and active override values are **OPEN**.

`MatchGenerator` scans eight columns and eight rows. Each line calls Matcher start (`0x84867c`), advance (`0x848740`), and finish (`0x848918`). Emit (`0x848944`) creates a raw run only for length >=3 (`0x848964`). Matcher start accepts a nonnull gem with nonzero effective color and numeric kind `gem+0x34 !=4`. Advance additionally invokes Gem slot `+0xe8`, concretely `0x84127c`:

```python
eligible = (gem.byte_25 != 0
            and gem.byte_12 == 0
            and (gem.byte_bd == 0 or gem.byte_be != 0)
            and gem.byte_14 == 0
            and gem.byte_16 == 0
            and gem.byte_18 == 0
            and gem.kind_34 != 4)
```

**VERIFIED asymmetry:** The first position of each line uses start without this eligibility call. An otherwise ineligible nonzero-color, non-kind-4 first cell can therefore participate in a run if later cells pass advance. This is a local predicate asymmetry, not a demonstrated reachable bug. The independent model includes an explicit fixture for it.

For ordinary colors the reconstruction is contiguous equal-color runs, broken by empty/ineligible cells. Numeric color **8** has special compatibility behavior: an active color 8 adopts the next effective color; an incoming 8 can extend a run; a trailing sequence of 8s can be retained as the start of a subsequent differently colored run. Relevant matcher fields are current color `+0x10`, last gem `+0x60`, count `+0x68`, start `+0x6c`, write position `+0x70`, and retained-tail start `+0x74`.

```text
advance(gem, override):                     # 0x848740, structural pseudocode
  color = override if nonzero else gem.color
  if absent, color == 0, or not eligible(gem):
      emit_if_length_at_least_3(); reset(); start(null); return
  if no active last gem: start(gem, override); return
  if active_color == 8: active_color = color; append(gem); return
  if color == active_color:
      tail_start = run_start; append(gem); return
  if color == 8:
      if no retained tail: tail_start = write_position
      append(gem); return
  if no retained tail:
      emit_if_length_at_least_3(); reset(); start(gem, override); return
  emit_if_length_at_least_3()                # 0x8488f4..0x8488fc
  active_color = color
  run_start = tail_start
  run_count = write_position - tail_start
  append(gem)
```

After raw runs, the generator links/group results. Raw Match initialization `0x8586f8` calculates member bounds and marks member byte `+0xc2`. Overlap predicate `0x8588ec` compares the four axis-aligned bounds at Match `+0x4c/+0x50/+0x54/+0x58`; it is not simply a pointer-intersection test. The model checks raw-match **existence**, not exact grouped MatchSet membership, ordering, ranks, pool effects, or special-color results. User-facing names and exhaustive semantics of numeric 8/4 remain **OPEN**.

### VERIFIED: move scanning, `0x86ef38` -> `0x86f08c`

The `MoveFinder` vtable starts at `0x17cb478`; slot `+0x30` is `0x86ef38`, slot `+0x38` is worker `0x86f08c`. The scan clears gem bytes `+0xc1/+0xc3` and visits nonnull cells. An anchor participates only if its rules object (`gem+0x28`) has byte `+0xd !=0`.

| Direction from anchor | Adjacent target's required rules byte | Anchor's direct-activation byte | Ordinary supporting pairs, flat offsets from anchor (`row*8+col`) |
|---|---|---|---|
| Up | `+0xb` | `+0xe` | `(-10,-9)`, `(-9,-7)`, `(-7,-6)`, `(-16,-24)` |
| Right | `+0xc` | `+0xf` | `(-15,-7)`, `(-7,9)`, `(9,17)`, `(2,3)` |
| Down | `+0x9` | `+0x10` | `(6,7)`, `(7,9)`, `(9,10)`, `(16,24)` |
| Left | `+0xa` | `+0x11` | `(-17,-9)`, `(-9,7)`, `(7,15)`, `(-2,-3)` |

Native row/column guards prevent wraparound. The target must exist and permit entry in that direction. A direct-activation anchor byte can then generate a move without color-pair tests. Otherwise the worker tests the listed patterns and creates results through `0x86fc3c`.

Support predicate `0x86fb60` requires a nonnull, eligible supporting gem and accepts equal raw colors, supporting kind 5, or anchor kind 5. Pair helper `0x86fbd0` adds a constraint when the anchor is kind 5: the two supporting gems' raw colors must equal. It also marks anchor/support bytes. In this special case later ordered pair-helper calls can replace a previous return status; a simple OR over all patterns is not established for every special type. **OPEN:** full kind-5 move semantics and rules-object construction.

For the modeled ordinary subset, the pattern rule is equivalent to placing the anchor at the adjacent destination, vacating the source, and requiring a three-cell line through the destination with two matching eligible supporters. It does not require a different destination color. It is a directed-anchor calculation, rather than an unrestricted simulation of every consequence of a swap. The reverse directed anchor can account for another side of a swap; exact result deduplication/counts are not modeled.

```python
# Ordinary subset only: no color 8, kind 5, matching overrides, or pool effects.
def directed_move(anchor, direction):
    if not anchor.rules.scan_enabled: return False
    target = adjacent(anchor, direction)
    if target is None or not target.rules.entry[direction]: return False
    if anchor.rules.direct[direction]: return True
    return any(eligible(p) and eligible(q)
               and p.color == anchor.color == q.color
               for p, q in guarded_support_pairs(anchor, direction))
```

## Replacement branches and edge cases

**VERIFIED:** `0x8609a4` first calls Board `+0xd0` -> `0x85a408`; the returned vector holds replacement objects already inserted into the board. N is its pointer-span divided by eight. The model begins after this creation step and supplies those reset/preset objects itself.

```python
# Structural reconstruction of 0x8609a4, not executable native code.
new_gems = board.create_replacements()
if len(new_gems) == 0: return                 # 0x8609fc
if len(new_gems) == 1:
    options = copy(active_config.palette)    # config +0x1b0 -> scratch +0xe8
    for i in range(len(options)):
        j = rng_stream_1.index(len(options)) # entire palette at every i
        swap(options[i], options[j])         # not Fisher-Yates
    for color in options:                    # 0x860b4c..0x860b84
        new_gems[0].color = color
        if accept(board, A): break
    return                                   # also returns if none accepted
while True:                                  # 0x860a88 back-edge
    if not (B & 1):
        for gem in new_gems:
            gem.color = board.random_color(stream=1)
    if accept(board, A): return
```

| Edge case | VERIFIED local control flow / INFERRED consequence | Model coverage |
|---|---|---|
| No replacements | Return without validation or color RNG, for any flags | All four combinations |
| One replacement | Finite pass through shuffled palette entries; B has no effect here | Acceptance, rejection, all four combinations |
| Multiple replacements, B=0 | Assign every replacement from cached Board palette, then validate; retry after failure | Retry then acceptance; persistent-failure budget boundary |
| Multiple replacements, B=1 | Validate existing replacement colors; retry skips assignment | Successful preserve and unchanged-color failure cases |
| A=0, immediate match | Reject before move search, even if moves exist elsewhere | Strict rejection and next-candidate acceptance |
| A=1, immediate match | Match rejection skipped; a move is still required | Match-plus-move acceptance and no-move rejection |
| No available moves | Reject for either A. Single pass can exhaust; bulk retries | Both flags and both cardinalities represented |
| All single candidates rejected | Return normally leaving last attempted color; no success flag, rollback, or fallback in this routine | `candidate_exhausted` is a model diagnostic |
| Empty single palette | No candidate validation; return retaining supplied/reset color | Explicit empty-palette case |
| Empty bulk palette | No safe-domain guarantee established for RandomColor; cannot infer a valid color | Excluded from model random domain; **OPEN** native precondition/fallback |
| Bulk retry termination | No local cap/counter visible. B=1 does not alter colors or draw color RNG on retry | Harness stops at a declared budget, never reports this as native return |
| Pending gem state | Orchestrator can defer before creation/spawn | Deferral fixture with zero attempts/draws |
| Noneligible first scan cell | Start omits later eligibility predicate | Initial-cell versus middle-cell fixtures |
| Row/column edge | Native guards limit support accesses | Boundary and no-wrap fixtures |

**INFERRED:** A repeatedly invalid, unchanged-color bulk state has no termination guarantee supplied by this loop body. This is not a confirmed reachable hang: result pooling, state flags, callbacks, configuration preconditions, or an invariant outside this body may matter. Even B=0 has no deterministic finite bound established by repeated random attempts. Successful return from the single branch does not imply its final board passed validation.

**Flag combinations:** A controls acceptance, B controls bulk reassignment. For N>=2: `(0,0)` redraws until match-free plus moves; `(1,0)` redraws until moves; `(0,1)` keeps colors while requiring match-free plus moves; `(1,1)` keeps colors while requiring moves. For N=1, the two B values collapse to the same behavior. A=1 does not disable match generation elsewhere in the update pipeline.

## Palette selection and seed propagation

### VERIFIED: active versus cached palette

`0x85cac8` selects the active-configuration pointer at logic `+0x288`:

| Mode | Selected pointer |
|---|---|
| 0 | Pointer at logic `+0x280` |
| 1 | Object at logic `+0x290`, embedded configuration at `+8`, if nonnull; sets byte `logic+0x180` |
| 2 | Pointer at logic `+0x298` |
| Other | Existing pointer retained by this routine; byte `+0x180` is cleared |

Board reset `0x858c6c` snapshots active configuration `+0x1b0` into Board `+0x70`. Setup calls this reset before refill. The single-replacement branch copies the **current active configuration** palette; bulk `0x85a938` calls RandomColor `0x85ab94`, which reads the **Board snapshot**. These two source locations are independently visible. A configuration switch after the snapshot could produce divergent palettes (**INFERRED scenario**, not an observed session). Fixtures explicitly exercise the distinction. Complete `.colors` parsing, selection callers, sync timing, and user-facing mode names remain **OPEN**.

Experiment 02's RNG index/float caveats remain: stream 1 supplies replacement selection; full-span repeated swaps do not establish a uniform permutation; exact endpoint behavior and resulting probabilities need separate work. The model uses bounded scripted indices and rejects an out-of-range index rather than inventing native behavior.

### VERIFIED: seed record and reseeding consumer; OPEN: scheduling

Setup `0x85e3d4` saves its integer input, converts it to decimal at `0x85e7c0`, and queues a **-1** record through logic slot `+0x378` -> `0x861588` at `0x85e828`. Queueing is not itself reseeding.

Event dispatcher `0x86302c` parses the command integer and uses a halfword jump table at `0x48a0c6`, base `0x8631ac`, scaled by four. Command -1 resolves to `0x863424`. This handler parses the next decimal field (`0x863438`), calls RNG manager `+0x20` -> `0x86ec30` (`0x86344c`), and stores the parsed seed at logic `+0x418` (`0x863460`). Getter `0x8666c4` returns this field, as recorded in Experiment 02.

`0x86ec30` iterates its managed RNG wrappers, resets them and forwards the same integer to their seed method. Wrapper `0x8a5d84` forwards to underlying PRNG slot `+0x10`; the MT implementation is `0x83e6a4`. This extends the previous seed-field observation into a concrete command-to-manager propagation path. **OPEN:** the external source of setup's seed argument, all stream registrations, when this record is consumed relative to the first setup draw, and whether other paths reseed. No complete deterministic session sequence is claimed.

## Independent model and observed test results

Sources: [model](../models/refill_model.py), [runner](../scripts/run_experiment_03_model.py), [fixtures](../tests/fixtures/experiment-03-boards.json), [full results](evidence/experiment-03-model-results.json). All code and fixtures were written for this experiment; no game code, assets, captured boards, or output of a game session is used as a fixture. Color integers express a test domain, not recovered enum names.

**Supported domain:** 8×8, colors 1..7, kind 0 and kind-4 barriers, explicit eligibility and directional permissions, empty cells, zero matching overrides, supplied replacement objects, and scripted in-range indices. Native raw flags are summarized as explicit model inputs; no claim is made about their naturally occurring combinations. Wild color 8 and kind 5 fail explicitly at the model boundary.

**VERIFIED by running original code:** 57/57 cases passed. The suite covers the two baseline boards (one with no matches/moves and one with a move), validation short-circuiting, all flags at zero/one/bulk cardinalities, candidate exhaustion, empty candidates, retry budgets, palette source separation, matching eligibility asymmetry, permission gates/direct activation, all 16 support-pair shapes, boundaries, and three negative-domain checks. Each support fixture isolates the two same-color supporters and verifies that disabling either removes the directed move. The geometric and support-pair move sets are compared before every main fixture and after each modeled spawn, and on each support fixture and its disabled-support variants.

Examples of predictions checked against the reconstructed flow:

| Fixture behavior | Prediction and recorded result |
|---|---|
| Strict single candidate creates an immediate run | First candidate rejected; later color accepted when a move remains |
| Match allowed but board has no move | Still rejected; A does not bypass move validation |
| Single replacement with every color rejected | Finite exhaustion; last color remains; B does not change this |
| Invalid preserved bulk board | Repeats validation with zero assignment draws until **model** budget reached |
| Invalid randomized bulk board | More assignment draws and attempts until **model** budget reached |
| Cached Board palette differs from active configuration | Bulk uses cached palette; single branch uses active palette |
| Matching support at board edge | Geometric and native-pattern interpretations agree without row wrap |

**Comparison limit:** Agreement is between original executable models and manually reconstructed static rules. No native routine was invoked as an oracle. The suite does not prove equivalence over all boards, exact native result counts/order, wildcard logic, kind-5 ordered helper behavior, override masks, pool/marker side effects, compaction, preset creation, callback effects, exact PRNG output, or session reachability. Fixture retry budgets are harness safety boundaries, not reconstructed native limits. A blank model `accepted` value at that boundary means unresolved completion, not native failure.

## Reproduction instructions

Run from the repository root. Supply your own lawfully held exact-build artifact; it is intentionally absent here. Use a scratch directory excluded by `.gitignore`. The APK option reads the ARM64 member in memory and does not extract or execute it. An existing ELF is supported separately. The verifier refuses to overwrite files, including prior reports/listings.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r scripts/requirements-experiment-02.txt

# Recheck prior evidence, then inspect Experiment 03 facts.
.\.venv\Scripts\python scripts/verify_experiment_02.py --apk "C:\path\input.apk" --report work/baseline.json
.\.venv\Scripts\python scripts/verify_experiment_03.py --apk "C:\path\input.apk" --report work/static-apk.json --listing-dir work/listings03

# Alternative: the exact already-extracted ARM64 member (read-only).
.\.venv\Scripts\python scripts/verify_experiment_03.py --elf "C:\path\libBejBlitz.so" --report work/static-elf.json

# No proprietary input or third-party dependency is needed for the model.
python scripts/run_experiment_03_model.py --report work/model-results.json
```

Review the generated local function listings alongside each evidence checkpoint group: `receiver_binding`, `update_gates`, `pending_gates`, `setup_flags`, `cardinality_and_retries`, `acceptance`, `match_scan`, `matcher_rules`, `eligibility`, `match_bounds`, `move_gates`, `support_predicate`, `support_offsets`, `palette_switch`, and `seed_pipeline`. Reconstruct indirect calls from the relocation entries and constructor bindings; a branch annotation is not a substitute for inspecting its surrounding instructions. The jump table should independently resolve -1 to `0x863424`.

The static verifier validates hashes, architecture/build ID, FDE lengths, function digests, relocations, decoded instructions, jump-table bytes and unchanged input hash. Use a fresh output path on reruns. Hash-gate rejection of a different input is expected, not evidence about that input's behavior. The original APK and analysis ELF retained their recorded hashes after investigation.

## Findings ledger and recommended Experiment 04

| Classification | Finding |
|---|---|
| VERIFIED | Concrete app-to-logic receiver chain; `(1,0)` update call; setup `(0,B)` derivation; two other refill contexts; pending-state deferral |
| VERIFIED | Optional immediate-match rejection followed by mandatory positive move count; eligibility, overrides, threshold and ordinary support patterns |
| VERIFIED | Zero/single/bulk distinctions; finite single exhaustion; no visible bulk retry bound; B does not bypass single trials |
| VERIFIED | Active versus cached palette sources; -1 record consumer reaches RNG reseeding and stored seed |
| VERIFIED, original model | 57 passing hand-authored cases and fixture-level agreement of two ordinary move calculations |
| INFERRED | Cascade/setup/preset context descriptions; possible palette divergence after a configuration switch; lack of a local termination guarantee for persistently invalid bulk states |
| OPEN | Runtime reachability/frequency; exact event meanings; rules-object and override writers; special types; external seed provenance and first-draw timing; externally enforced termination invariants |

**Experiment 04: Refill Preconditions, Preset Palettes, and Seed Ordering.** Keep the same static-only boundary and exact-build gates. Follow configuration/rules-object construction and matching-override writes into the specific setup paths already identified; map active rare-object slot `+0xe8` implementations; establish which palette/preset invariants can make preserved bulk validation succeed. Trace dispatch of the queued -1 seed record to its consumer and order that consumption against the first stream-1 draw. Extend the original model only where these traces justify new rules, with hand-authored cases for wildcard-tail overlap and kind-5 ordered pair handling if their prerequisites are resolved. The deliverable should be an event/precondition graph and explicit termination/seed-order contracts or unresolved boundaries. No unrelated scoring, online systems, or adaptive-difficulty claim is needed.
