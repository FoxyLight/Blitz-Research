#!/usr/bin/env python3
"""Exact-build static checks for Experiment 03. Reads bytes; never loads native code."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
import capstone
import elftools
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from elftools.dwarf.callframe import FDE

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--apk', type=Path)
    g.add_argument('--elf', type=Path)
    p.add_argument('--evidence', type=Path, default=ROOT / 'research/evidence/experiment-03-arm64.json')
    p.add_argument('--report', type=Path)
    p.add_argument('--listing-dir', type=Path)
    args = p.parse_args()
    source = (args.apk or args.elf).resolve()
    spec = json.loads(args.evidence.read_text(encoding='utf-8'))
    initial = source.read_bytes()
    initial_hash = digest(initial)
    checks = []

    def equal(label, actual, expected):
        checks.append({'check': label, 'pass': actual == expected})
        if actual != expected:
            raise ValueError(f'{label}: {actual!r} != {expected!r}')

    def output(path, content):
        path = path.resolve()
        if path in (source, args.evidence.resolve(), Path(__file__).resolve()) or path.exists():
            raise ValueError(f'Refusing to overwrite {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')

    try:
        if args.apk:
            equal('APK SHA-256 gate', initial_hash, spec['apk_sha256'])
            with zipfile.ZipFile(io.BytesIO(initial)) as z:
                data = z.read(spec['member'])
        else:
            data = initial
        equal('ELF SHA-256 gate', digest(data), spec['elf_sha256'])
        elf = ELFFile(io.BytesIO(data))
        equal('Architecture', elf['e_machine'], spec['architecture'])
        equal('64-bit little endian', [elf.elfclass, elf.little_endian], [64, True])
        notes = elf.get_section_by_name('.note.gnu.build-id')
        equal('Build ID', next(n['n_desc'] for n in notes.iter_notes() if n['n_type'] == 'NT_GNU_BUILD_ID'), spec['build_id'])
        loads = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']

        def read(va, size):
            for s in loads:
                if s['p_vaddr'] <= va and va + size <= s['p_vaddr'] + s['p_filesz']:
                    offset = s['p_offset'] + va - s['p_vaddr']
                    return data[offset:offset + size]
            raise ValueError(f'Unmapped file-backed range {va:#x}+{size}')

        fdes = {f['initial_location']: f['address_range'] for f in elf.get_dwarf_info().EH_CFI_entries() if isinstance(f, FDE)}
        md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        for f in spec['functions']:
            a = int(f['address'], 16)
            equal(f"FDE {f['address']}", fdes.get(a), f['size'])
            equal(f"Function digest {f['address']}", digest(read(a, f['size'])), f['sha256'])
        relocs = {}
        for s in elf.iter_sections():
            if s['sh_type'] == 'SHT_RELA':
                for r in s.iter_relocations():
                    relocs[r['r_offset']] = [r['r_info_type'], r['r_addend']]
        for r in spec['relocations']:
            equal(f"Relocation {r['address']}", relocs.get(int(r['address'], 16)), [r['type'], int(r['addend'], 16)])
        for group in spec['checkpoints']:
            for i in group['instructions']:
                a = int(i['address'], 16)
                x = next(md.disasm(read(a, 4), a), None)
                equal(f"{group['id']} {i['address']}", [x.mnemonic, x.op_str] if x else None, [i['mnemonic'], i['operands']])
        decoded_tables = []
        for table in spec['jump_tables']:
            values = list(struct.unpack('<' + 'H' * len(table['entries']), read(int(table['address'], 16), 2 * len(table['entries']))))
            equal(f"Jump table {table['address']}", values, table['entries'])
            decoded_tables.append({str(table['first_case'] + n): hex(int(table['base'], 16) + value * table['scale']) for n, value in enumerate(values)})
        equal('Source unchanged', digest(source.read_bytes()), initial_hash)
        if args.listing_dir:
            for f in spec['functions']:
                a = int(f['address'], 16)
                lines = [f"{f['label']} [{f['address']},{f['end']})"]
                lines += [f'{x.address:08x}: {x.mnemonic:9} {x.op_str}' for x in md.disasm(read(a, f['size']), a)]
                output(args.listing_dir / f'{a:08x}.asm.txt', '\n'.join(lines) + '\n')
        report = {'status': 'PASS', 'python': sys.version.split()[0], 'capstone': capstone.__version__, 'pyelftools': elftools.__version__,
                  'source_sha256': initial_hash, 'elf_sha256': digest(data), 'checks_passed': len(checks),
                  'function_ranges': len(spec['functions']), 'instruction_checkpoints': sum(len(g['instructions']) for g in spec['checkpoints']),
                  'relocations': len(spec['relocations']), 'decoded_jump_tables': decoded_tables, 'checks': checks,
                  'limits': 'Byte/structure verification only; not native execution, runtime reachability, or semantic equivalence testing.'}
        if args.report:
            output(args.report, json.dumps(report, indent=2) + '\n')
        print(f"PASS: {len(checks)} static checks; {len(spec['functions'])} FDE ranges; {report['instruction_checkpoints']} instruction sites; {report['relocations']} relocations")
        return 0
    except (ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(run())
