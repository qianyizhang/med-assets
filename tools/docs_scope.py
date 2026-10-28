#!/usr/bin/env python3
"""Select a conservative prose-only PR scope; uncertainty selects full checks."""
import re
import subprocess
import sys

PROSE = {'CONTRIBUTING.md'}


def git(*args):
    return subprocess.run(['git', *args], check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).stdout


def docs_only(base, head):
    try:
        merge = git('merge-base', base, head).strip().decode('ascii')
        records = git('diff', '--no-renames', '--name-status', '-z', merge, head).split(b'\0')
        if not records or records[-1] != b'' or len(records) < 3 or len(records) % 2 != 1:
            return False
        for status, raw_path in zip(records[0:-1:2], records[1:-1:2]):
            path = raw_path.decode('utf-8')
            if status not in (b'A', b'M') or path not in PROSE:
                return False
            for revision in (merge, head) if status == b'M' else (head,):
                entry = git('ls-tree', revision, '--', path).split(b'\t', 1)[0].split()
                if len(entry) != 3 or entry[0] != b'100644' or entry[1] != b'blob':
                    return False
                content = git('show', f'{revision}:{path}').decode('utf-8')
                # No executable examples or embedded active content in the fast path.
                if re.search(r'`|(?m:^\s*~~~|^(?: {4}|\t))|<\s*(?:script|iframe|object)\b', content, re.I):
                    return False
        return True
    except (subprocess.CalledProcessError, UnicodeError, ValueError):
        return False


if __name__ == '__main__':
    if len(sys.argv) != 3 or not docs_only(sys.argv[1], sys.argv[2]):
        print('full')
    else:
        print('docs')
