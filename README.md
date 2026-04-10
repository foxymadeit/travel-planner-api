# Travel Planner API



Travellers create projects (trips), populate them with artworks from the [Art Institute of Chicago](https://www.artic.edu/) collection, leave notes, and mark places as visited. When every place in a project is visited the project is automatically marked as completed.


---

## Project structure

```
app/
├── main.py              # App entry point, router registration
├── database.py          # SQLAlchemy engine & session
├── models.py            # ORM models (Project, Place)
├── schemas.py           # Pydantic request/response schemas
├── routers/
│   ├── projects.py      # Project endpoints
│   └── places.py        # Place endpoints
└── services/
    └── artwork_api.py   # Art Institute of Chicago API client
```

---

## Getting started

### Option A — run locally

**Requirements:** Python 3.9+

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/travel-planner-api.git
cd travel-planner-api

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**

---

### Option B — run with Docker

**Requirements:** Docker + Docker Compose

```bash
docker compose up --build
```

The API will be available at **http://localhost:8000**

---

## Environment variables

All variables are optional — the app works with the defaults shown below.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./travel.db` | SQLAlchemy database URL |

---

## API documentation

FastAPI generates interactive documentation automatically.

| Interface | URL |
|---|---|
| **Swagger UI** (try endpoints live) | http://localhost:8000/docs |
| **ReDoc** (clean reference) | http://localhost:8000/redoc |
| **OpenAPI JSON spec** | http://localhost:8000/openapi.json |

---

## Endpoints

### Projects

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/projects` | Create a project (optionally with places) |
| `GET` | `/api/v1/projects` | List all projects |
| `GET` | `/api/v1/projects/{id}` | Get a single project |
| `PUT` | `/api/v1/projects/{id}` | Update project details |
| `DELETE` | `/api/v1/projects/{id}` | Delete project (blocked if any place is visited) |

### Places

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/projects/{id}/places` | Add a place to a project |
| `GET` | `/api/v1/projects/{id}/places` | List all places in a project |
| `GET` | `/api/v1/projects/{id}/places/{place_id}` | Get a single place |
| `PATCH` | `/api/v1/projects/{id}/places/{place_id}` | Update notes / mark as visited |

---

## Example requests

### Create a project
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicago Art Tour",
    "description": "Impressionist masterpieces",
    "start_date": "2025-06-01"
  }'
```

### Create a project with places in one request
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicago Art Tour",
    "place_ids": [27992, 28560]
  }'
```

### Add a place to an existing project
```bash
curl -X POST http://localhost:8000/api/v1/projects/1/places \
  -H "Content-Type: application/json" \
  -d '{"external_id": 27992}'
```

> `external_id` is the artwork ID from the Art Institute of Chicago API.  
> The API validates the artwork exists before saving it.

### Some real artwork IDs to try

| external_id | Artwork |
|---|---|
| `27992` | Georges Seurat — A Sunday on La Grande Jatte |
| `28560` | Edward Hopper — Nighthawks |

### Update notes and mark a place as visited
```bash
curl -X PATCH http://localhost:8000/api/v1/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Stunning use of colour. Worth every minute.",
    "is_visited": true
  }'
```

### List all projects
```bash
curl http://localhost:8000/api/v1/projects
```

---

## Business rules

- A project can have **1–10 places**
- The same artwork **cannot be added twice** to the same project
- A project **cannot be deleted** if any of its places are marked as visited
- When **all places** in a project are visited, the project is automatically marked as `is_completed: true`
- Every `external_id` is validated against the Art Institute of Chicago API before being stored
