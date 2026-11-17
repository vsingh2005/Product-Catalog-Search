# Products

Released operations: crud.

Fields and validation rules:

```json
{
  "sku": {
    "type": "TEXT",
    "required": true
  },
  "name": {
    "type": "TEXT",
    "required": true
  },
  "description": {
    "type": "TEXT",
    "required": true
  },
  "status": {
    "type": "TEXT",
    "required": true,
    "choices": [
      "draft",
      "active",
      "discontinued"
    ]
  }
}
```

API: `/api/products`. CSV import: POST `/api/products/import` with a JSON `csv` field when released. Summary: GET `/api/products/report` when released. Search: GET `/api/products?q=term&limit=50&offset=0` when released. PUT `/api/products/ID` accepts `record` and the last observed `version`; stale updates are rejected.
