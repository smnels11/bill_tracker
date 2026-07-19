# Bill Tracker

A lightweight Streamlit app backed by Postgres for tracking manual (non-autopay) bills.

## Project Structure

```text
.
├── app.py
├── .dockerignore
├── dockerfile.bills
├── docker-compose.yaml
├── pyproject.toml
├── utils.py
├── uv.lock
└── db/
    └── init.sql        <- Postgres runs this once on first boot
```

## Getting Started

### Build and start the containers

```bash
docker compose up --build -d
```

Access the app at **http://localhost:8501**.


## Using the App

- **Add a bill** — expand the form, fill in name, due date, and whether it repeats monthly. The amount is recorded when you mark it paid, so variable bills (e.g., electric) work naturally.
- **Mark as Paid** — expand an unpaid bill row and click ✅. If it's monthly, next month's entry is created automatically (due dates on the 29th–31st clamp to the last day of shorter months).
- **Delete** — removes the bill entirely (use for one-offs you added by mistake).
- **Payment history** — expand the bottom section to see the last 50 paid entries.

**Note:** The Streamlit container uses bind mounts for `app.py` and `utils.py`, allowing live code updates during development. Once the containers are running, changes made to either `.py` file will be reflected after refreshing the Streamlit app in your browser. This makes it easy to experiment with the application without rebuilding the Docker image. In particular, the `bill_dict` defined near the top of `app.py` contains example bill entries. Users are encouraged to replace these placeholders with their own bill information.

If these files are moved or renamed, update the corresponding `volumes` paths in `docker-compose.yaml`.

## Accessing the Database Directly

```bash
docker exec -it bills_db psql -U bills_user -d bills_db
```

View all unpaid bills:
```sql
SELECT * FROM bills WHERE is_paid = FALSE ORDER BY due_date;
```

View payment history:
```sql
SELECT * FROM bills WHERE is_paid = TRUE ORDER BY paid_at DESC;
```

Export to CSV:
```sql
COPY bills TO '/tmp/bills.csv' CSV HEADER;
```

Exit the SQL shell:
```sql
\q
```

Then copy out of the container:
```bash
docker cp bills_db:/tmp/bills.csv .
```