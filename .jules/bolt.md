## 2024-05-15 - N+1 Queries in SQLAlchemy Reports
**Learning:** When generating reports that aggregate data across relationships (like fetching open invoices and their associated customer details), lazy loading causes severe N+1 query bottlenecks.
**Action:** Always use `.options(joinedload(...))` for relationship fields that will be accessed inside loops during report generation.
