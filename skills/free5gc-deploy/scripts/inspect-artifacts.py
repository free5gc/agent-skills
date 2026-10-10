#!/usr/bin/env python3
"""Conservative inert Makefile inspection; never invoke make or shell expressions."""
import argparse
import os
from pathlib import Path
import re


def inspect(repo):
    try:
        path = repo / 'Makefile'
        if not path.exists():
            return [('UNKNOWN', 'artifacts', 'Makefile absent; expected outputs not established')]
        if path.stat().st_size > 100_000:
            return [('UNKNOWN', 'artifacts', 'Makefile outside bounded inspection scope')]
        text = path.read_text()
        # Recognize the reviewed Go-only shape. Arbitrary Makefile languages and
        # legacy C-UPF require manual inspection, never evaluation.
        assignments = {}
        for key in ('GO_NF', 'GO_BIN_PATH', 'NF', 'WEBCONSOLE', 'WEBCONSOLE_FRONTEND'):
            matches = re.findall(r'^' + key + r'\s*([:+?]?=)\s*([^\n]+)$', text, re.M)
            if len(matches) != 1 or matches[0][0] not in ('=', ':='):
                return [('UNKNOWN', 'artifacts', 'unsupported Makefile definitions')]
            assignments[key] = matches[0][1].strip()
        names = assignments['GO_NF'].split()
        binpath = assignments['GO_BIN_PATH']
        if (not names or len(names) > 64 or len(set(names)) != len(names)
                or any(not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', n) for n in names)
                or not re.fullmatch(r'[a-zA-Z0-9_-]+', binpath)
                or assignments['NF'] != '$(GO_NF)'
                or assignments['WEBCONSOLE'] != 'webconsole'
                or assignments['WEBCONSOLE_FRONTEND'] != '$(WEBCONSOLE)/public'
                or '$(GO_BIN_PATH)/%:' not in text
                or '-o $(ROOT_PATH)/$@ main.go' not in text
                or not re.search(r'^all:\s*\$\(NF\)\s+\$\(WEBCONSOLE\)\s*$', text, re.M)
                or '$(WEBCONSOLE)/$(GO_BIN_PATH)/$(WEBCONSOLE):' not in text
                or '-o $(ROOT_PATH)/$@ ./server.go' not in text
                or re.search(r'^\s*(?:include|-include|sinclude|override|define|C_NF\s*[:?+]?=)', text, re.M)):
            return [('UNKNOWN', 'artifacts', 'unsupported Makefile layout; inspect selected version')]
        outputs = [Path(binpath) / n for n in names]
        outputs += [Path('webconsole') / binpath / 'webconsole', Path('webconsole/public/index.html')]
        results = []
        for relative in outputs:
            target = repo / relative
            # Do not print user-controlled source fields or follow paths outside repo.
            if not target.resolve().is_relative_to(repo.resolve()):
                results.append(('UNKNOWN', 'artifact', 'output symlink outside repo'))
            else:
                try:
                    metadata = target.stat()
                except FileNotFoundError:
                    results.append(('FAIL', 'artifact', f'missing {relative}'))
                    continue
                except OSError:
                    results.append(('UNKNOWN', 'artifact', f'cannot observe {relative}'))
                    continue
                if not target.is_file() or not os.access(target, os.R_OK):
                    results.append(('UNKNOWN', 'artifact', f'unreadable/non-file {relative}'))
                elif metadata.st_size == 0:
                    results.append(('FAIL', 'artifact', f'empty {relative}'))
                elif relative.suffix != '.html' and not os.access(target, os.X_OK):
                    results.append(('FAIL', 'artifact', f'not executable {relative}'))
                else:
                    results.append(('PASS', 'artifact', f'present {relative}; existence only'))
        return results
    except (OSError, UnicodeError):
        return [('UNKNOWN', 'artifacts', 'Makefile/output inaccessible')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    rows = inspect(parser.parse_args().repo)
    for state, key, evidence in rows:
        print(f'{state} [{key}] {evidence}')
    return 1 if any(r[0] == 'FAIL' for r in rows) else 2 if any(r[0] == 'UNKNOWN' for r in rows) else 0


if __name__ == '__main__':
    raise SystemExit(main())
