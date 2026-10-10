# Lab Equipment Borrowing API

A REST API built with **FastAPI** & **SQLite** 

**Features**

- Manage categories, equipment, and borrowers (create, read, update, delete)
- Search, filter, and page through equipment, borrowers, and loans
- Borrow several items in one all-or-nothing transaction (stock is updated automatically)
- Return equipment with an automatic late penalty for students and faculty

---

## 1. Requirements

- Python **3.10 or newer** (check with `python --version`, or `py --version` on Windows)
- Git

No database server is needed: SQLite is built into Python.

## 2. Setup

### 2.1 Clone the repository

```bash
git clone https://github.com/<your-username>/fastapi-it5.git
cd fastapi-it5
```

### 2.2 Create and activate a virtual environment

Run the commands for your system from inside the project folder (the one that contains `main.py`).

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses to run the activation script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**macOS / Linux (bash or zsh)**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Linux with the fish shell**

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
```

When it works, your prompt starts with `(.venv)`.

### 2.3 Install the requirements

```bash
python -m pip install -r requirements.txt
```

or, with uv:

```bash
uv pip install -r requirements.txt
```

### 2.4 Run the application

```bash
uvicorn main:app --reload
```

You should see a line like `Uvicorn running on http://127.0.0.1:8000`. Press `Ctrl+C` to stop it.

### 2.5 Open the interactive documentation

Open **http://127.0.0.1:8000/docs** in a browser. This Swagger page lists every endpoint and lets you test them without writing any client code.

### 2.6 The database

The first time the app starts it creates a SQLite file named **`equipment.db`** next to `main.py` and creates all the tables. Data is kept between restarts.

To start again from an empty database: stop the server, delete `equipment.db`, and start the server again. **Do this before section 5**, so the ids in the examples match yours.

---

## 3. Using the API

On the `/docs` page, click an endpoint, press **Try it out**, edit the request body or fill in the parameters, then press **Execute**. The result appears under **Server response**. Errors come back as `{"detail": "..."}` with a message explaining what went wrong.

## 4. Project structure

```
main.py                  creates the app and registers the routers
requirements.txt
app/
    database.py          SQLite connection and table creation
    models.py            Pydantic models (input validation)
    exceptions.py        custom errors
    repositories.py      all the SQL, one class per table
    services.py          borrow / return workflows and penalty policies
    routers/
        categories.py
        equipment.py
        borrowers.py
        loans.py
```

---

## 5. Sample tests for every endpoint

Do the tests **in order, starting from an empty database** (see 2.6). Part A is the normal flow, Part B the error cases, and Part C the rules that involve several tables.

### Part A: Normal flow

#### A1. Home

`GET /` returns `{"message": "Welcome! Visit /docs to try the API."}`

#### A2. Categories

**Create** `POST /categories`
```json
{"name": "Microscopes", "description": "Optical instruments"}
```
The new category comes back with `"id": 1`. Create two more, one at a time:
```json
{"name": "Cables"}
```
```json
{"name": "Temporary"}
```

**List** `GET /categories` returns the 3 categories.

**Get one** `GET /categories/1` returns "Microscopes".

**Replace** `PUT /categories/2`
```json
{"name": "Cables and Adapters", "description": "Power and data cables"}
```

**Delete** `DELETE /categories/3`. Then `GET /categories/3` reports that it was not found.

#### A3. Equipment

Each row is a type of item with a stock count, not a single physical unit.

**Create** `POST /equipment`
```json
{"name": "Compound microscope", "category_id": 1, "description": "40x to 1000x", "quantity_total": 5}
```
It comes back with `"id": 1`, `"quantity_available": 5` (a new item starts with every unit available), and `"category_name": "Microscopes"`. Create two more:
```json
{"name": "HDMI cable", "category_id": 2, "description": "2 meter cable", "quantity_total": 2}
```
```json
{"name": "Stereo microscope", "category_id": 1, "quantity_total": 3}
```

**List and search** `GET /equipment`. Try these one at a time in the parameter fields:

| Parameters | Result |
|---|---|
| none | all 3 items |
| `q` = `microscope` | items 1 and 3 (searches name and description, ignores case) |
| `category_id` = `2` | item 2 only |
| `available_only` = `true` | all 3 (all have units available) |
| `skip` = `1`, `limit` = `1` | item 2 only (paging) |

**Get one** `GET /equipment/1`

**Replace** `PUT /equipment/2`
```json
{"name": "HDMI cable 2m", "category_id": 2, "description": "2 meter cable", "quantity_total": 4}
```
The result shows `quantity_total` 4 and `quantity_available` 4.

**Delete** `DELETE /equipment/3`

#### A4. Borrowers

**Create** `POST /borrowers`
```json
{"full_name": "Ana Cruz", "borrower_type": "student", "id_number": "2024-0001", "contact": "ana@school.edu"}
```
It comes back with `"id": 1`. Create two more:
```json
{"full_name": "Prof. Reyes", "borrower_type": "faculty", "id_number": "EMP-0100"}
```
```json
{"full_name": "Ben Lim", "borrower_type": "student", "id_number": "2024-0002"}
```
(`contact` is optional and comes back as `null` when left out.)

**List and search** `GET /borrowers`

| Parameters | Result |
|---|---|
| none | all 3 borrowers |
| `q` = `cruz` | Ana Cruz only (searches name and id number) |
| `borrower_type` = `faculty` | Prof. Reyes only |

**Get one** `GET /borrowers/1`

**Replace** `PUT /borrowers/3`
```json
{"full_name": "Benjamin Lim", "borrower_type": "student", "id_number": "2024-0002", "contact": "09171234567"}
```

**Delete** `DELETE /borrowers/3`

#### A5. Loans (borrow and return)

**Borrow** `POST /loans` (one request can borrow several items)
```json
{
  "borrower_id": 1,
  "items": [
    {"equipment_id": 1, "quantity": 2},
    {"equipment_id": 2, "quantity": 1}
  ],
  "notes": "Lab activity"
}
```
The loan comes back with `"id": 1`, `"status": "active"`, a `due_date` 7 days from today (used when none is sent), and both items listed.
Check the stock: `GET /equipment/1` now shows `quantity_available` **3**, and `GET /equipment/2` shows **3**.

**List and search** `GET /loans`

| Parameters | Result |
|---|---|
| none | the 1 loan |
| `status` = `active` | the 1 loan |
| `borrower_id` = `1` | the 1 loan |
| `q` = `cruz` | the 1 loan (searches the borrower's name and id number) |

**Get one** `GET /loans/1` shows the borrower's name and the items.

**Return** `POST /loans/1/return` (no body). The loan shows `"status": "returned"`, today's `returned_date`, and `"penalty_amount": 0`.
Check the stock again: `GET /equipment/1` is back to **5** and `GET /equipment/2` to **4**. Also try `GET /loans?status=returned`.

---

### Part B: Error cases to try

Run these after Part A. Each request should be rejected as shown.

#### Categories

| Request | Body / parameter | Result |
|---|---|---|
| `POST /categories` | `{"name": "microscopes"}` | "A category with this name already exists" (case is ignored) |
| `POST /categories` | `{"name": ""}` | invalid (name must be 1 to 100 characters) |
| `POST /categories` | `{"name": "Lab", "color": "red"}` | invalid (unknown field) |
| `POST /categories` | `{}` | invalid (name is required) |
| `GET /categories/{id}` | `99` | "Category 99 not found" |
| `GET /categories/{id}` | `abc` | invalid (id must be a number) |
| `PUT /categories/{id}` | `99` with `{"name": "Z"}` | not found |
| `PUT /categories/{id}` | `2` with `{"name": "Microscopes"}` | name already used by category 1 |
| `DELETE /categories/{id}` | `99` | not found |
| `DELETE /categories/{id}` | `1` | "Category 1 is still used by other records and cannot be deleted" (it has equipment) |

#### Equipment

Use this body as the base: `{"name": "Test", "category_id": 1, "quantity_total": 1}`

| Request | Change | Result |
|---|---|---|
| `POST /equipment` | `"category_id": 99` | "Category 99 not found" |
| `POST /equipment` | `"quantity_total": 0` | invalid (must be at least 1) |
| `POST /equipment` | add `"quantity_available": 3` | invalid (stock is controlled by borrowing, not typed in) |
| `POST /equipment` | `"name": ""` | invalid |
| `GET /equipment/{id}` | `99` | not found |
| `GET /equipment` | `limit` = `0` or `101` | invalid (limit must be 1 to 100) |
| `PUT /equipment/{id}` | `99` with the base body | not found |
| `DELETE /equipment/{id}` | `99` | not found |

#### Borrowers

Use this body as the base: `{"full_name": "Someone", "borrower_type": "student", "id_number": "NEW-1"}`

| Request | Change | Result |
|---|---|---|
| `POST /borrowers` | `"id_number": "2024-0001"` | "A borrower with this id number already exists" |
| `POST /borrowers` | `"borrower_type": "teacher"` | invalid (only `student` or `faculty`) |
| `GET /borrowers/{id}` | `99` | "Borrower 99 not found" |
| `GET /borrowers` | `borrower_type` = `teacher` | invalid |
| `PUT /borrowers/{id}` | `1` with `{"full_name": "Ana Cruz", "borrower_type": "student", "id_number": "EMP-0100"}` | id number already belongs to Prof. Reyes |
| `DELETE /borrowers/{id}` | `99` | not found |
| `DELETE /borrowers/{id}` | `1` | refused (Ana has a loan on record) |

#### Loans

| Request | Body / parameter | Result |
|---|---|---|
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 99}]}` | "Not enough 'Compound microscope': requested 99, available 5" |
| `POST /loans` | `{"borrower_id": 99, "items": [{"equipment_id": 1, "quantity": 1}]}` | "Borrower 99 not found" |
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 99, "quantity": 1}]}` | "Equipment 99 not found" |
| `POST /loans` | `{"borrower_id": 2, "items": []}` | invalid (at least one item) |
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 1}, {"equipment_id": 1, "quantity": 1}]}` | invalid (same equipment twice) |
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 0}]}` | invalid |
| `POST /loans` | `{"borrower_id": 2, "due_date": "2020-01-01", "items": [{"equipment_id": 1, "quantity": 1}]}` | invalid (due date in the past) |
| `POST /loans` | `{"borrower_id": 2, "due_date": "2099-01-01", "items": [{"equipment_id": 1, "quantity": 1}]}` | invalid (more than 14 days away) |
| `POST /loans/{id}/return` | `1` (already returned) | "Loan 1 was already returned" |
| `POST /loans/{id}/return` | `99` | not found |
| `GET /loans/{id}` | `99` | "Loan 99 not found" |
| `GET /loans` | `status` = `lost` | invalid (only `active`, `overdue`, `returned`) |

---

### Part C: Rules that involve several tables

Run these after Part B, in order.

#### C1. A failed borrow is undone completely (transaction rollback)

`POST /loans`
```json
{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 1}, {"equipment_id": 2, "quantity": 99}]}
```
It is refused with "Not enough 'HDMI cable 2m': requested 99, available 4". The first item was valid, but the whole borrow is all-or-nothing. Check: `GET /equipment/1` still shows `quantity_available` **5**, and `GET /loans` still lists only **1** loan.

#### C2. Make an active loan

`POST /loans`
```json
{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 2}]}
```
It comes back with `"id": 2`, and `GET /equipment/1` now shows `quantity_available` **3**.

#### C3. Units on loan are protected

- `PUT /equipment/1` with `{"name": "Compound microscope", "category_id": 1, "description": "40x to 1000x", "quantity_total": 1}` is refused: "2 unit(s) are currently borrowed, so quantity_total cannot be lower than 2".
- `DELETE /equipment/1` is refused (this equipment appears in loans).

#### C4. Overdue loans and penalties

The API only creates loans dated today, so to see a late loan we move loan 2's dates into the past. With the virtual environment active, in the project folder, start Python by typing `python`, then paste these lines:

```python
import sqlite3
con = sqlite3.connect("equipment.db")
con.execute("UPDATE loans SET borrowed_date = date('now','localtime','-10 days'), due_date = date('now','localtime','-3 days') WHERE id = 2")
con.commit()
con.close()
exit()
```

Then in Swagger:

1. `GET /loans/2` shows `"status": "overdue"` and `"days_overdue": 3`. `GET /loans?status=overdue` lists loan 2.
2. `POST /loans` with `{"borrower_id": 2, "items": [{"equipment_id": 2, "quantity": 1}]}` is refused, because a borrower with an overdue loan cannot borrow again.
3. `POST /loans/2/return` shows `"status": "returned"`, `"days_overdue": 3`, and `"penalty_amount": 5`.
   Borrower 2 is faculty: the first 2 late days are a grace period, then the rate is 5 pesos per day, so 3 days late costs 5. A **student** pays 10 pesos per late day from the first day (3 days late would cost 30).
4. Repeat the request from step 2. It now works, because the overdue loan was returned.