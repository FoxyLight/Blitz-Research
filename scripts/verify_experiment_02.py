#!/usr/bin/env python3
"""Read-only, exact-build static verifier. Never loads or executes native code."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

import capstone
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
import elftools
from elftools.elf.elffile import ELFFile
from elftools.dwarf.callframe import FDE


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--apk', type=Path, help='Locally owned, original APK')
    group.add_argument('--elf', type=Path, help='Previously extracted ARM64 ELF')
    parser.add_argument('--evidence', type=Path, default=Path(__file__).resolve().parents[1] / 'research/evidence/experiment-02-arm64.json')
    parser.add_argument('--report', type=Path, help='Write JSON validation results')
    parser.add_argument('--extract-dir', type=Path, help='With --apk, write only the selected library here, after identity checks')
    parser.add_argument('--listing-dir', type=Path, help='Write local disassembly for the recorded functions; keep out of Git')
    args = parser.parse_args()
    spec = json.loads(args.evidence.read_text(encoding='utf-8'))
    source = (args.apk or args.elf).resolve()
    source_bytes = source.read_bytes()
    source_hash = sha(source_bytes)
    checks = []

    def check(name, actual, expected):
        ok = actual == expected
        checks.append({'check': name, 'pass': ok, 'actual': actual, 'expected': expected})
        if not ok:
            raise ValueError(f'{name}: expected {expected!r}, got {actual!r}')

    def output_path(path):
        resolved = path.resolve()
        if resolved in (source, args.evidence.resolve(), Path(__file__).resolve()):
            raise ValueError('Refusing to overwrite an input file')
        if resolved.exists():
            raise ValueError(f'Refusing to overwrite existing output: {resolved}')
        return resolved

    try:
        if args.apk:
            check('APK SHA-256', source_hash, spec['apk_sha256'])
            with zipfile.ZipFile(io.BytesIO(source_bytes)) as archive:
                data = archive.read(spec['member'])
        else:
            if args.extract_dir:
                raise ValueError('--extract-dir requires --apk')
            data = source_bytes
        check('ELF SHA-256', sha(data), spec['elf_sha256'])
        check('ELF size', len(data), spec['elf_size'])
        elf = ELFFile(io.BytesIO(data))
        check('ELF architecture', elf['e_machine'], spec['architecture'])
        check('ELF little endian', elf.little_endian, True)
        check('ELF 64-bit', elf.elfclass, 64)
        note = elf.get_section_by_name('.note.gnu.build-id')
        build_id = next(n['n_desc'] for n in note.iter_notes() if n['n_type'] == 'NT_GNU_BUILD_ID')
        check('GNU build ID', build_id, spec['build_id'])
        loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']

        def read(va, size):
            for segment in loads:
                if segment['p_vaddr'] <= va and va + size <= segment['p_vaddr'] + segment['p_filesz']:
                    offset = segment['p_offset'] + va - segment['p_vaddr']
                    return data[offset:offset + size]
            raise ValueError(f'Unmapped file-backed address: {va:#x}')

        fdes = {f['initial_location']: f['address_range'] for f in elf.get_dwarf_info().EH_CFI_entries() if isinstance(f, FDE)}
        md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        for function in spec['functions']:
            va = int(function['address'], 16)
            size = function['size']
            check(f"FDE range {va:#x}", fdes.get(va), size)
            check(f"Function digest {va:#x}", sha(read(va, size)), function['sha256'])
            if va in (0x885eb0, 0x85ab94, 0x888374, 0x8609a4):
                executable = any(s['p_vaddr'] <= va and va + size <= s['p_vaddr'] + s['p_filesz'] and s['p_flags'] & 1 for s in loads)
                check(f'Executable mapping {va:#x}', bool(executable), True)

        relocs = {}
        for section in elf.iter_sections():
            if section['sh_type'] == 'SHT_RELA':
                for r in section.iter_relocations():
                    relocs[r['r_offset']] = (r['r_info_type'], r['r_addend'])
        for r in spec['relocations']:
            va = int(r['address'], 16)
            actual = relocs.get(va)
            check(f'Relocation {va:#x}', list(actual) if actual else None, [r['type'], int(r['addend'], 16)])
        for group_spec in spec['checkpoints']:
            for expected in group_spec['instructions']:
                va = int(expected['address'], 16)
                ins = next(md.disasm(read(va, 4), va), None)
                actual = [ins.mnemonic, ins.op_str] if ins else None
                check(f"{group_spec['id']} {va:#x}", actual, [expected['mnemonic'], expected['operands']])

        literals = {
            0x48ac3c: 'N9BlitzCore15RandomGemPickerE',
            0x48acd9: 'N9BlitzCore16GemPickerManagerE',
            0x48abf3: 'N9BlitzCore23FinisherStateControllerE',
            0x48a024: 'N9BlitzCore5BoardE',
            0x48a0da: 'N9BlitzCore10BlitzLogicE',
            0x48994f: 'N9BlitzCore15MersenneTwisterE',
            0x48b8e2: 'N9BlitzCore11BlitzRandomE',
            0x48ad3c: 'N9BlitzCore16PatternGemPickerE',
            0x48a301: 'N9BlitzCore10MoveFinderE',
            0x432698: '0',
        }
        for va, expected in literals.items():
            check(f'Literal {va:#x}', read(va, len(expected) + 1), (expected + '\0').encode())
        # Bytes are represented as text in the JSON report.
        for item in checks:
            for key in ('actual', 'expected'):
                if isinstance(item[key], bytes):
                    item[key] = item[key].decode('ascii')
        check('Input SHA-256 unchanged', sha(source.read_bytes()), source_hash)
        if args.extract_dir:
            target = output_path(args.extract_dir / 'libBejBlitz-arm64.so')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if args.listing_dir:
            for function in spec['functions']:
                va = int(function['address'], 16)
                target = output_path(args.listing_dir / f'{va:08x}.asm.txt')
                target.parent.mkdir(parents=True, exist_ok=True)
                lines = [f"{function['label']} [{function['address']}, {function['end']})"]
                lines += [f'{i.address:08x}: {i.mnemonic:9} {i.op_str}' for i in md.disasm(read(va, function['size']), va)]
                target.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        result = {'status': 'PASS', 'tools': {'python': sys.version.split()[0], 'capstone': capstone.__version__, 'pyelftools': elftools.__version__}, 'source_sha256': source_hash, 'elf_sha256': sha(data), 'checks_passed': len(checks), 'functions': len(spec['functions']), 'instruction_checkpoints': sum(len(g['instructions']) for g in spec['checkpoints']), 'relocations': len(spec['relocations']), 'checks': checks}
        if args.report:
            target = output_path(args.report)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(f"PASS: {len(checks)} checks; {len(spec['functions'])} function ranges/digests; {result['instruction_checkpoints']} instruction checkpoints; {result['relocations']} relocations")
        return 0
    except (ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
