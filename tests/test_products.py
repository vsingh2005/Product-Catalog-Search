import csv
import io
import json
from pathlib import Path
import pytest
from operations import Store


def test_resource_workflow(tmp_path):
    root = Path(__file__).resolve().parents[1]
    definitions = [json.loads(p.read_text()) for p in sorted((root / 'resources').glob('*.json'))]
    store = Store(str(tmp_path / 'app.db'), definitions)
    ids = {}

    def seed(name):
        if name in ids:
            return ids[name]
        spec = store.spec(name)
        row = {}
        for key, rule in spec['fields'].items():
            if 'reference' in rule:
                row[key] = seed(rule['reference'])
            elif 'choices' in rule:
                row[key] = rule['choices'][0]
            else:
                row[key] = 'Sample item' if rule['type'] == 'TEXT' else 2
        ids[name] = store.create(name, row)
        return ids[name]

    try:
        name = 'products'
        spec = store.spec(name)
        record_id = seed(name)
        record = store.list(name)[0]
        payload = {key: record[key] for key in spec['fields']}
        store.update(name, record_id, payload, record['version'])
        with pytest.raises(ValueError, match='stale'):
            store.update(name, record_id, payload, record['version'])
        with pytest.raises(ValueError):
            store.create(name, {})
        with pytest.raises(ValueError):
            store.create(name, dict(payload, unexpected='field'))
        with pytest.raises(ValueError):
            store.list(name, limit=10000)
        for key, rule in spec['fields'].items():
            if 'reference' in rule:
                with pytest.raises(ValueError, match='missing'):
                    store.create(name, dict(payload, **{key: 999999}))
        if 'import' in spec['operations']:
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=list(payload))
            writer.writeheader()
            writer.writerow(payload)
            assert len(store.import_csv(name, stream.getvalue())) == 1
            before = len(store.list(name))
            writer.writerow({key: '' for key in payload})
            with pytest.raises(ValueError):
                store.import_csv(name, stream.getvalue())
            assert len(store.list(name)) == before
        if 'report' in spec['operations']:
            assert store.report(name)['count'] == len(store.list(name))
        if 'search' in spec['operations']:
            assert store.list(name, query="' OR 1=1 --") == []
            text_key = next(key for key, rule in spec['fields'].items() if rule['type'] == 'TEXT')
            assert store.list(name, query=str(payload[text_key]).lower())
        assert store.db.execute('SELECT COUNT(*) FROM audit WHERE resource=?', (name,)).fetchone()[0] >= 2
    finally:
        store.close()
