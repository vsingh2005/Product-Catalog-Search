# Product Catalog and Search

Maintain a retail catalog, import supplier records, track variants and availability, and search products.

## Status

Year-one local prototype under scheduled development. Features below are planned until their task is committed. No production readiness or ML performance is claimed.

## Run

`python app.py` then open http://127.0.0.1:8000 after the foundation release.
Tests: `python -m pytest -q` after installing pytest. Runtime uses the Python standard library and SQLite.

## Year-one schedule

| Due date | Milestone |
|---|---|
| 2026-11-17 | Add persistent operations API with validated records and audit history |
| 2026-11-26 | Document versioned record API and validation responses |
| 2026-12-03 | Add browser workspace for record entry and table views |
| 2026-12-10 | Add products transactional CSV imports |
| 2026-12-17 | Add products summary reporting |
| 2026-12-24 | Add products paginated text search |
| 2026-12-31 | Add suppliers record management |
| 2027-01-07 | Add suppliers transactional CSV imports |
| 2027-01-14 | Add suppliers summary reporting |
| 2027-01-21 | Add suppliers paginated text search |
| 2027-01-28 | Add categories record management |
| 2027-02-05 | Add categories transactional CSV imports |
| 2027-02-12 | Add categories summary reporting |
| 2027-02-19 | Add categories paginated text search |
| 2027-02-26 | Add variants record management |
| 2027-03-05 | Add variants transactional CSV imports |
| 2027-03-12 | Add variants summary reporting |
| 2027-03-19 | Add variants paginated text search |
| 2027-03-26 | Add inventory record management |
| 2027-04-02 | Add inventory transactional CSV imports |
| 2027-04-09 | Add inventory summary reporting |
| 2027-04-17 | Add inventory paginated text search |
| 2027-04-24 | Add prices record management |
| 2027-05-01 | Add prices transactional CSV imports |
| 2027-05-08 | Add prices summary reporting |
| 2027-05-15 | Add prices paginated text search |
| 2027-05-22 | Add supplier items record management |
| 2027-05-29 | Add supplier items transactional CSV imports |
| 2027-06-05 | Add supplier items summary reporting |
| 2027-06-12 | Add supplier items paginated text search |
| 2027-06-19 | Add product matches record management |
| 2027-06-27 | Add product matches transactional CSV imports |
| 2027-07-04 | Add product matches summary reporting |
| 2027-07-11 | Add product matches paginated text search |
| 2027-07-18 | Add product attributes record management |
| 2027-07-25 | Add product attributes transactional CSV imports |
| 2027-08-01 | Add product attributes summary reporting |
| 2027-08-08 | Add product attributes paginated text search |
| 2027-08-15 | Add ratings record management |
| 2027-08-22 | Add ratings transactional CSV imports |
| 2027-08-29 | Add ratings summary reporting |
| 2027-09-06 | Add ratings paginated text search |
| 2027-09-13 | Add search events record management |
| 2027-09-20 | Add search events transactional CSV imports |
| 2027-09-27 | Add search events summary reporting |
| 2027-10-04 | Add search events paginated text search |
| 2027-10-11 | Add recommendations record management |
| 2027-10-18 | Add recommendations transactional CSV imports |
| 2027-10-25 | Add recommendations summary reporting |
| 2027-11-01 | Add recommendations paginated text search |
| 2027-11-08 | Run application tests and lint on pushes and pull requests |
| 2027-11-16 | Document backup recovery and limits for local operations |

Daily automation checks eligibility, validates a pending release, and retries failures without advancing its task. There are 52 milestones over 365 days. Dates are earliest release dates, not guarantees.

## Longer-term product work

After the operational foundation, evaluate hosted authentication, PostgreSQL migrations, deployment, domain-specific workflow rules, and measured ML features. These are not implemented by the year-one task list.
