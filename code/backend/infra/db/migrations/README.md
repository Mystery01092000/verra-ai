# Database migrations

Add numbered `.sql` migration files here, e.g.:

```
0001_add_tax_brackets.sql
0002_add_user_sessions.sql
```

Run migrations with:

```bash
export DATABASE_URL=postgres://verra:verra@localhost:5432/verra
cd code/backend/infra/db
python migrate.py
```

Migrations are tracked in the `schema_migrations` table and applied only once.
