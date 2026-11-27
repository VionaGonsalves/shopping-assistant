# Shopping Assistant

A car shop backend with an AI chat assistant. Customers can ask things like *"How much is the Honda City?"* or *"Add it to my cart"*, and the assistant answers from live data and acts on their cart, using only the permissions of the logged-in user.

Built with **FastAPI**, **PostgreSQL**, **MCP (Model Context Protocol)** and **Claude**.

> Proof of concept, built as a learning project for LLM integration and MCP.

---

## Features

- **REST API** for products and carts (FastAPI, SQLAlchemy, PostgreSQL)
- **JWT authentication** with hashed passwords (Argon2)
- **Role-based authorisation**: customers browse and shop; only admins can create or change products
- **MCP server** exposing three tools: `search_products`, `get_price`, `add_to_cart`
- **Chat endpoint** where Claude decides which tools to call, in a loop, until it can answer
- **Per-user conversation memory**, so follow-ups like *"yes, add it"* work
- **Guardrails**: prices only from tool results, confirmation before adding to the cart

---

## Architecture

**How a chat request flows:**

1. The user sends a message to `POST /chat` with their JWT.
2. The endpoint checks the token, then starts the MCP server **with that user's token** in its environment.
3. It sends Claude the conversation, the system prompt and the MCP tool list.
4. If Claude asks for a tool, the endpoint runs it through MCP. The tool calls the REST API as the user, and the result goes back to Claude.
5. This repeats (up to 5 rounds) until Claude replies with text, which is returned to the user.

---

## Tech stack

- Python 3.12, FastAPI, Uvicorn
- SQLAlchemy 2, PostgreSQL 16 (Docker)
- Pydantic v2, pydantic-settings
- PyJWT, pwdlib (Argon2)
- MCP Python SDK (FastMCP, pinned `<2`), httpx
- Anthropic Python SDK (Claude)

---

## Project structure

```
shopping-assistant/
├── app/
│   ├── main.py          # app setup, lifespan, routers
│   ├── config.py        # settings from .env
│   ├── db.py            # engine, session, get_db
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── auth.py          # hashing, JWT, get_current_user, require_admin
│   ├── seed.py          # demo data
│   └── routers/
│       ├── auth.py      # register, login, me
│       ├── products.py  # list/search, get, create, update
│       ├── cart.py      # view, add, update, remove
│       └── chat.py      # Claude + MCP tool loop, conversation memory
├── mcp_server/
│   └── server.py        # MCP tools calling the REST API
├── LEARNINGS.md
└── requirements.txt
```

---

## Running locally

**Prerequisites:** Python 3.12+, Docker (or Colima on macOS), Node.js (for the MCP Inspector), an Anthropic API key.

```bash
# 1. Install
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start Postgres
docker run --name shop-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=shop -p 5432:5432 -d postgres:16

# 3. Configure .env (see below)

# 4. Run the API (creates tables on startup)
uvicorn app.main:app --reload

# 5. Seed demo data (in another terminal)
python -m app.seed
```

Open **http://localhost:8000/docs** for the interactive API.

### `.env`

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/shop
SECRET_KEY=<output of: openssl rand -hex 32>
ACCESS_TOKEN_EXPIRE_MINUTES=30
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5-5
```

### Demo users (local only)

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@shop.com` | `admin123` |
| Customer | `viona@shop.com` | `customer123` |

---

## API overview

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | none | Create a customer account |
| POST | `/auth/login` | none | Get a JWT (form data: `username` = email) |
| GET | `/auth/me` | user | Current user |
| GET | `/products?q=&product_type=&limit=&offset=` | none | Search and list cars |
| GET | `/products/{id}` | none | One car |
| POST | `/products` | admin | Create a car |
| PATCH | `/products/{id}` | admin | Update a car (only fields sent) |
| GET | `/cart` | user | View your cart |
| POST | `/cart/items` | user | Add a car (increases quantity if already there) |
| PATCH | `/cart/items/{id}` | user | Change quantity |
| DELETE | `/cart/items/{id}` | user | Remove an item |
| POST | `/chat` | user | Send a message to the assistant: `{"message": "..."}` |
| DELETE | `/chat` | user | Clear your conversation |

---

## Trying the assistant

In `/docs`, click **Authorize** and log in as the customer, then call `POST /chat`:

```json
{"message": "How much is the Honda City?"}
```

```json
{"message": "Yes, add it to my cart"}
```

Then check `GET /cart`. Log in as the customer and try `PATCH /products/1` to see the **403**: the chat assistant has the same limits.

### Testing the MCP server on its own

```bash
mcp dev mcp_server/server.py
```

Open the link it prints, connect, and call the tools from the **Tools** tab. For `add_to_cart`, put a valid `SHOP_API_TOKEN` in `.env` (the server loads it with `python-dotenv`).

---
