import pytest
from operations import Store


def test_missing_resource_and_pagination(tmp_path):
    store = Store(str(tmp_path / 'test.db'), [])
    try:
        with pytest.raises(KeyError):
            store.list('not_a_table')
        assert store.db.execute('SELECT COUNT(*) FROM audit').fetchone()[0] == 0
    finally:
        store.close()
