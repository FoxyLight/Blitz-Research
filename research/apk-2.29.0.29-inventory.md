# APK inventory: Bejeweled Blitz 2.29.0.29

**Status:** VERIFIED for inventory, hashes, manifest values, and literal strings.  
**Inspection date:** 2026-10-29  
**Source:** User-supplied Android APK, locally named `com.ea.BejeweledBlitz.com.apk`; **not redistributed**.

## Artifact identity

| Field | Observed value |
|---|---|
| File size | 126,485,803 bytes |
| SHA-256 | `1b9c3c6b9eb25a3de568802b5242f838e7618425c70b09c4a7fac00408a8f8b4` |
| APK ZIP entries | 2,002 |
| Android manifest package | `com.ea.BejeweledBlitz_na` |
| Android manifest versionName | `2.29.0.29` |
| Android manifest versionCode | `995` |
| Manifest compileSdkVersion | `34` |

**Reproduction:** Inspect the ZIP using Python's `zipfile`; hash the complete APK using SHA-256; decode the binary `AndroidManifest.xml` to obtain the package and version values. Do not infer the package from the local filename (which differs from the manifest).

## Native libraries

| APK path | Uncompressed size |
|---|---:|
| `lib/arm64-v8a/libBejBlitz.so` | 26,337,872 bytes |
| `lib/armeabi-v7a/libBejBlitz.so` | 19,985,928 bytes |

The ARM64 library is an AArch64 little-endian ELF shared object. Its GNU build ID is `f03da685fe6dd40cb0f322b118225931c4407c91`.

A check of the ARM64 section headers shows `.dynsym` but no ordinary `.symtab`. This limits recovery of original named functions; strings and C++-style type names remain useful leads, not finished decompilation.

The archive also has `classes.dex` through `classes5.dex` and `assets/audience_network.dex`. Their presence does not establish where any particular game rule is implemented.

## Literal strings observed in ARM64 library

The following names or type-name substrings occur in binary string data:

- Board/matches: `Board`, `GemGrid`, `Matcher`, `MatchGenerator`, `MoveFinder`, `MovePolicy`
- Selection: `RandomGemPicker`, `PatternGemPicker`, `GemPickerManager`
- Random numbers: `BlitzRNGManager`, `MersenneTwister`, `ParkMillerLCG`
- Scores/effects: `BlitzScoreKeeper`, `MatchScore`, `CascadeScore`, `HypercubeLogic`, `FlameGemLogic`, `StarGemLogic`

Particularly relevant literal log strings:

```text
REPLAY : getRandomBoard
REPLAY : SpawnGems optionIndex
REPLAY : RandomColor :
REPLAY : RandomGemPicker columnId :
REPLAY : RandomGemPicker rowId :
REPLAY : ScrambleGems
```

**Caution:** Presence in the executable confirms only that the bytes exist; it does not prove a path runs in normal gameplay or reveal the precise implementation. The `REPLAY` prefix hints at replay-related instrumentation, but its behavior is not yet established.

## Asset examples

The APK contains resources such as:

```text
assets/COCOS_COMMONIMAGES_GEMS_1X.rsg.smf
assets/COCOS_COMMONIMAGES_GEMS_2X.rsg.smf
assets/EXP_GAMECOREGEMS.rsg.smf
assets/EXP_GAMECOREGEMS_3X.rsg.smf
```

These file paths establish that such resource files are packaged. Their names alone do not identify the engine or gameplay algorithm.

## Tools used for this verification

Python standard library (`zipfile`, `hashlib`, `struct`), GNU `readelf`, and binary string inspection. **Ghidra was not used for this verification.** No APK or native code was executed or installed.

## Follow-up verification

- Identify executable code references to the `RandomGemPicker` and `SpawnGems` strings.
- Obtain a reproducible function map using Ghidra or an equivalent AArch64 analysis tool.
- Reconstruct caller/callee relationships and validate them against observed gameplay.
