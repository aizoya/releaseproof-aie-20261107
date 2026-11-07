import argparse
import json
from pathlib import Path
from .core import MAX_SOURCE
from .store import Store, GateBlocked

def main():
    parser = argparse.ArgumentParser(description='ReleaseProof bounded verification')
    parser.add_argument('--db', default='.state/evidence.sqlite3')
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('verify')
    check.add_argument('candidate', type=Path)
    accept = commands.add_parser('accept')
    accept.add_argument('run_id')
    accept.add_argument('candidate_sha256')
    show = commands.add_parser('show')
    show.add_argument('run_id')
    prepare = commands.add_parser('prepare-meta')
    prepare.add_argument('candidate', type=Path)
    imported = commands.add_parser('import-meta')
    imported.add_argument('response', type=Path)
    serve = commands.add_parser('serve')
    serve.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if args.command == 'serve':
        from .server import serve
        serve(args.db, args.port)
        return
    store = Store(args.db)
    try:
        if args.command == 'prepare-meta':
            from .proposals import prepare_meta_request
            with args.candidate.open('rb') as stream: raw=stream.read(MAX_SOURCE+1)
            if len(raw)>MAX_SOURCE: parser.error('Candidate is too large.')
            print(json.dumps(prepare_meta_request(raw.decode('utf-8')),indent=2))
        elif args.command == 'import-meta':
            from .proposals import import_meta_response, MAX_RESPONSE
            with args.response.open('rb') as stream: raw=stream.read(MAX_RESPONSE+1)
            source,provenance=import_meta_response(raw)
            report=store.submit(source,provenance=provenance)
            print(json.dumps(report,indent=2))
            raise SystemExit({'pass':0,'fail':1,'inconclusive':2}[report['status']])
        elif args.command == 'verify':
            with args.candidate.open('rb') as stream: raw = stream.read(MAX_SOURCE + 1)
            if len(raw) > MAX_SOURCE: parser.error('Candidate is too large.')
            report = store.submit(raw.decode('utf-8'))
            print(json.dumps(report, indent=2))
            raise SystemExit({'pass': 0, 'fail': 1, 'inconclusive': 2}[report['status']])
        elif args.command == 'accept':
            print(json.dumps(store.accept(args.run_id, args.candidate_sha256), indent=2))
        else:
            print(json.dumps(store.get(args.run_id), indent=2))
    except (ValueError, KeyError, OSError, UnicodeError) as exc:
        print(json.dumps({'gate': 'blocked', 'reason': str(exc)}))
        raise SystemExit(2)

if __name__ == '__main__': main()
