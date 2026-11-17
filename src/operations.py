"""Small local-first operations API used by the portfolio applications.

Only bind to localhost. Authentication and hosted deployment are separate work.
"""
import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class Store:
    def __init__(self, database, definitions):
        self.definitions = {item['name']: item for item in definitions}
        self.db = sqlite3.connect(database)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.execute('PRAGMA busy_timeout = 5000')
        self.db.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, resource TEXT, record_id INTEGER, action TEXT, occurred_at TEXT)')
        for name, spec in self.definitions.items():
            fields = ', '.join(f'"{key}" {value["type"]}' for key, value in spec['fields'].items())
            self.db.execute(f'CREATE TABLE IF NOT EXISTS "{name}" (id INTEGER PRIMARY KEY, {fields}, version INTEGER NOT NULL DEFAULT 1)')
        self.db.commit()

    def close(self):
        self.db.close()

    def spec(self, name, operation=None):
        if name not in self.definitions:
            raise KeyError('Unknown resource')
        spec = self.definitions[name]
        if operation and operation not in spec['operations']:
            raise KeyError('Operation not released')
        return spec

    def validate(self, name, record):
        spec = self.spec(name)
        if not isinstance(record, dict) or set(record) - set(spec['fields']):
            raise ValueError('Unknown fields or invalid record')
        result = {}
        for key, rule in spec['fields'].items():
            value = record.get(key)
            if value is None:
                if rule.get('required'):
                    raise ValueError(f'{key} is required')
                result[key] = None
                continue
            if rule['type'] in ('INTEGER', 'REAL'):
                if isinstance(value, bool):
                    raise ValueError(f'{key} must be numeric')
                try:
                    number = float(value)
                    if not __import__('math').isfinite(number):
                        raise ValueError('Non-finite value')
                    if rule['type'] == 'INTEGER' and not number.is_integer():
                        raise ValueError('Expected integer')
                    value = int(number) if rule['type'] == 'INTEGER' else number
                except (ValueError, TypeError, OverflowError):
                    raise ValueError(f'{key} must be numeric') from None
                if 'min' in rule and value < rule['min']:
                    raise ValueError(f'{key} is below minimum')
            else:
                if not isinstance(value, str) or not value.strip() or len(value) > 2000:
                    raise ValueError(f'{key} must be nonempty text under 2001 characters')
                value = value.strip()
            if 'choices' in rule and value not in rule['choices']:
                raise ValueError(f'{key} is not an allowed value')
            if 'reference' in rule:
                target = rule['reference']
                self.spec(target)
                if not self.db.execute(f'SELECT id FROM "{target}" WHERE id=?', (value,)).fetchone():
                    raise ValueError(f'{key} references a missing record')
            result[key] = value
        return result

    def _insert(self, name, record):
        values = self.validate(name, record)
        keys = ','.join(f'"{key}"' for key in values)
        marks = ','.join('?' for _ in values)
        cursor = self.db.execute(f'INSERT INTO "{name}" ({keys}) VALUES ({marks})', tuple(values.values()))
        self.db.execute('INSERT INTO audit(resource,record_id,action,occurred_at) VALUES (?,?,?,?)',
                        (name, cursor.lastrowid, 'create', datetime.now(timezone.utc).isoformat()))
        return cursor.lastrowid

    def create(self, name, record):
        self.spec(name, 'crud')
        with self.db:
            return self._insert(name, record)

    def list(self, name, limit=50, offset=0, query=None):
        spec = self.spec(name, 'search' if query else 'crud')
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError('Invalid pagination')
        where, params = '', []
        if query:
            columns = [key for key, rule in spec['fields'].items() if rule['type'] == 'TEXT']
            if not columns:
                return []
            where = ' WHERE ' + ' OR '.join(f'instr(lower("{key}"), lower(?)) > 0' for key in columns)
            params = [query] * len(columns)
        rows = self.db.execute(f'SELECT * FROM "{name}"{where} ORDER BY id LIMIT ? OFFSET ?', (*params, limit, offset))
        return [dict(row) for row in rows]

    def update(self, name, record_id, record, version):
        self.spec(name, 'crud')
        values = self.validate(name, record)
        fields = ','.join(f'"{key}"=?' for key in values)
        with self.db:
            cursor = self.db.execute(f'UPDATE "{name}" SET {fields},version=version+1 WHERE id=? AND version=?',
                                     (*values.values(), record_id, version))
            if cursor.rowcount != 1:
                raise ValueError('Record missing or stale version')
            self.db.execute('INSERT INTO audit(resource,record_id,action,occurred_at) VALUES (?,?,?,?)',
                            (name, record_id, 'update', datetime.now(timezone.utc).isoformat()))

    def import_csv(self, name, text):
        spec = self.spec(name, 'import')
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('Missing or duplicate CSV headers')
        if set(reader.fieldnames) != set(spec['fields']):
            raise ValueError('CSV headers must match resource fields')
        ids = []
        with self.db:
            for row in reader:
                if len(ids) >= 1000:
                    raise ValueError('Import limited to 1000 rows')
                ids.append(self._insert(name, {key: value if value != '' else None for key, value in row.items()}))
        return ids

    def report(self, name):
        spec = self.spec(name, 'report')
        result = {'count': self.db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0], 'totals': {}, 'groups': {}}
        for key, rule in spec['fields'].items():
            if rule['type'] in ('INTEGER', 'REAL') and 'reference' not in rule:
                result['totals'][key] = self.db.execute(f'SELECT COALESCE(SUM("{key}"),0) FROM "{name}"').fetchone()[0]
            if 'choices' in rule:
                rows = self.db.execute(f'SELECT "{key}",COUNT(*) FROM "{name}" GROUP BY "{key}"')
                result['groups'][key] = {str(row[0]): row[1] for row in rows}
        return result


def serve(root, database='app.sqlite3', port=8000):
    root = Path(root)
    definitions = [json.loads(path.read_text()) for path in sorted((root / 'resources').glob('*.json'))]

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, code, value):
            data = json.dumps(value).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def handle_request(self):
            route = urlparse(self.path)
            if self.command == 'GET' and route.path == '/health':
                return self.send_json(200, {'status': 'ok'})
            if self.command == 'GET' and route.path == '/resources':
                return self.send_json(200, definitions)
            if self.command == 'GET' and route.path == '/':
                page = root / 'web' / 'index.html'
                if page.exists():
                    data = page.read_bytes()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    return self.wfile.write(data)
                return self.send_json(200, {'resources': '/resources', 'health': '/health'})
            parts = route.path.strip('/').split('/')
            if len(parts) not in (2, 3) or parts[0] != 'api':
                return self.send_json(404, {'error': 'Unknown endpoint'})
            store = Store(database, definitions)
            try:
                name = parts[1]
                store.spec(name)
                if self.command == 'GET':
                    if len(parts) == 3 and parts[2] == 'report':
                        return self.send_json(200, store.report(name))
                    if len(parts) != 2:
                        raise KeyError('Unknown endpoint')
                    params = parse_qs(route.query)
                    return self.send_json(200, store.list(name, int(params.get('limit', ['50'])[0]),
                                                         int(params.get('offset', ['0'])[0]), params.get('q', [None])[0]))
                # Browser cross-origin requests must not mutate a local database.
                origin = self.headers.get('Origin')
                if origin and origin != f'http://127.0.0.1:{port}':
                    return self.send_json(403, {'error': 'Cross-origin writes disabled'})
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1048576:
                    raise ValueError('Body must be between 1 byte and 1 MiB')
                body = json.loads(self.rfile.read(length))
                if self.command == 'POST' and len(parts) == 2:
                    return self.send_json(201, {'id': store.create(name, body)})
                if self.command == 'POST' and parts[2] == 'import':
                    return self.send_json(201, {'ids': store.import_csv(name, body['csv'])})
                if self.command == 'PUT' and len(parts) == 3:
                    store.update(name, int(parts[2]), body['record'], body['version'])
                    return self.send_json(200, {'updated': True})
                raise KeyError('Unknown endpoint')
            except KeyError as error:
                self.send_json(404, {'error': str(error)})
            except (ValueError, TypeError, sqlite3.IntegrityError) as error:
                self.send_json(400, {'error': str(error)})
            finally:
                store.close()

        do_GET = handle_request
        do_POST = handle_request
        do_PUT = handle_request

    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
