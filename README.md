# Lab Equipment Borrowing API

A REST API built with **FastAPI** and **SQLite** that replaces a paper logbook in a school laboratory. It keeps track of equipment stock, registers borrowers (students and faculty), and handles borrowing and returning: stock goes down when equipment is borrowed, goes back up when it is returned, and late returns are charged a penalty.

**Author:** _your name_  
**Course:** _course name_

The full description of the system (purpose, scope, and endpoint table) is in the project documentation (.docx). This file explains how to install, run, and test the application.

---

## 1. Requirements

- Python **3.10 or newer** (check with `python --version`, or `py --version` on Windows)
- Git
- An internet connection (to download the packages)

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

### 2.4 Run the application

```bash
python -m uvicorn main:app --reload
```

You should see a line like `Uvicorn running on http://127.0.0.1:8000`. The `--reload` option restarts the server automatically when a file changes. Press `Ctrl+C` to stop it.

### 2.5 Open the interactive documentation

Open **http://127.0.0.1:8000/docs** in a browser. This Swagger page lists every endpoint and lets you test them without writing any client code.

### 2.6 The database

The first time the app starts it creates a SQLite file named **`equipment.db`** next to `main.py` and creates all the tables. Data is kept between restarts.

To start again from an empty database: stop the server, delete `equipment.db`, and start the server again. **Do this before section 5**, so the ids in the examples match yours.

---

## 3. How to use the Swagger page

1. Click an endpoint to open it (for example `POST /categories`).
2. Click **Try it out**.
3. For endpoints with a body, replace the example JSON with the one you want to send. For endpoints with parameters (like `{category_id}` or filters), type the values into the fields.
4. Click **Execute**.
5. Read the result under **Server response**: the status code and the JSON body.

**Status codes used by this API**

| Code | Meaning |
|---|---|
| 200 | OK (data returned or updated) |
| 201 | Created (a new record was saved) |
| 204 | Deleted (success, no body) |
| 404 | The record (or a record it refers to) does not exist |
| 409 | Conflict: the request clashes with existing data (duplicate, record in use, not enough stock...) |
| 422 | Invalid input: a required field is missing or a value breaks a rule |

Error responses look like `{"detail": "Category 99 not found"}`.

## 4. Project structure

```
main.py                  creates the app, registers the routers and the error handlers
requirements.txt         the packages to install
app/
    database.py          SQLite connection (one transaction per request) and table creation
    models.py            Pydantic models: validation rules for input and output
    exceptions.py        custom errors (NotFoundError, ConflictError, InsufficientStockError)
    repositories.py      all the SQL, as classes (one repository per table)
    services.py          the borrow/return workflows and the penalty policy classes
    routers/
        categories.py    /categories endpoints
        equipment.py     /equipment endpoints
        borrowers.py     /borrowers endpoints
        loans.py         /loans endpoints
```

---

## 5. Sample tests for every endpoint

Do the tests **in order, starting from an empty database** (see 2.6). Each test says what to send and what you should see. Part A is the normal flow, Part B tries the error cases, and Part C tests the rules that involve several tables.

### Part A: Normal flow

#### A1. Home

`GET /` -> **200** `{"message": "Welcome! Visit /docs to try the API."}`

#### A2. Categories

**Create** `POST /categories`
```json
{"name": "Microscopes", "description": "Optical instruments"}
```
Expect **201** with `"id": 1`. Create two more (send them one at a time):
```json
{"name": "Cables"}
```
```json
{"name": "Temporary"}
```
Expect **201** with ids 2 and 3.

**List** `GET /categories` -> **200**, a list of 3 categories.

**Get one** `GET /categories/1` -> **200**, "Microscopes".

**Replace** `PUT /categories/2`
```json
{"name": "Cables and Adapters", "description": "Power and data cables"}
```
Expect **200** with the new name.

**Delete** `DELETE /categories/3` -> **204**. Then `GET /categories/3` -> **404**.

#### A3. Equipment

Each row is a type of item with a stock count, not a single physical unit.

**Create** `POST /equipment`
```json
{"name": "Compound microscope", "category_id": 1, "description": "40x to 1000x", "quantity_total": 5}
```
Expect **201** with `"id": 1`, `"quantity_available": 5` (a new item starts with every unit available) and `"category_name": "Microscopes"`. Create two more:
```json
{"name": "HDMI cable", "category_id": 2, "description": "2 meter cable", "quantity_total": 2}
```
```json
{"name": "Stereo microscope", "category_id": 1, "quantity_total": 3}
```
Expect **201** with ids 2 and 3.

**List and search** `GET /equipment`. Try these one at a time in the parameter fields:

| Parameters | Expect (**200**) |
|---|---|
| none | all 3 items |
| `q` = `microscope` | items 1 and 3 (searches name and description, ignores case) |
| `category_id` = `2` | item 2 only |
| `available_only` = `true` | all 3 (all have units available) |
| `skip` = `1`, `limit` = `1` | item 2 only (paging: skip 1, return 1) |

**Get one** `GET /equipment/1` -> **200**.

**Replace** `PUT /equipment/2`
```json
{"name": "HDMI cable 2m", "category_id": 2, "description": "2 meter cable", "quantity_total": 4}
```
Expect **200** with `quantity_total` 4 and `quantity_available` 4.

**Delete** `DELETE /equipment/3` -> **204**.

#### A4. Borrowers

**Create** `POST /borrowers`
```json
{"full_name": "Ana Cruz", "borrower_type": "student", "id_number": "2024-0001", "contact": "ana@school.edu"}
```
Expect **201** with `"id": 1`. Create two more:
```json
{"full_name": "Prof. Reyes", "borrower_type": "faculty", "id_number": "EMP-0100"}
```
```json
{"full_name": "Ben Lim", "borrower_type": "student", "id_number": "2024-0002"}
```
Expect **201** with ids 2 and 3 (`contact` is optional and comes back as `null`).

**List and search** `GET /borrowers`

| Parameters | Expect (**200**) |
|---|---|
| none | all 3 borrowers |
| `q` = `cruz` | Ana Cruz only (searches name and id number) |
| `borrower_type` = `faculty` | Prof. Reyes only |

**Get one** `GET /borrowers/1` -> **200**.

**Replace** `PUT /borrowers/3`
```json
{"full_name": "Benjamin Lim", "borrower_type": "student", "id_number": "2024-0002", "contact": "09171234567"}
```
Expect **200**.

**Delete** `DELETE /borrowers/3` -> **204**.

#### A5. Loans (borrow and return)

**Borrow** `POST /loans`: one request can borrow several items.
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
Expect **201** with `"id": 1`, `"status": "active"`, a `due_date` 7 days from today (used when you do not send one), and both items listed.
Now check the stock: `GET /equipment/1` shows `quantity_available` **3**, and `GET /equipment/2` shows **3**.

**List and search** `GET /loans`

| Parameters | Expect (**200**) |
|---|---|
| none | the 1 loan |
| `status` = `active` | the 1 loan |
| `borrower_id` = `1` | the 1 loan |
| `q` = `cruz` | the 1 loan (searches the borrower's name and id number) |

**Get one** `GET /loans/1` -> **200**, with the borrower's name and the items.

**Return** `POST /loans/1/return` (no body) -> **200** with `"status": "returned"`, today's `returned_date` and `"penalty_amount": 0`.
Check the stock again: `GET /equipment/1` is back to **5** and `GET /equipment/2` to **4**. Also try `GET /loans?status=returned` -> the 1 loan.

---

### Part B: Error cases to try

Run these after Part A. Each should fail in the way shown.

#### Categories

| Request | Body / parameter | Expected |
|---|---|---|
| `POST /categories` | `{"name": "microscopes"}` | **409** "A category with this name already exists" (case is ignored) |
| `POST /categories` | `{"name": ""}` | **422** (name must be 1 to 100 characters) |
| `POST /categories` | `{"name": "Lab", "color": "red"}` | **422** (unknown field) |
| `POST /categories` | `{}` | **422** (name is required) |
| `GET /categories/{id}` | `99` | **404** "Category 99 not found" |
| `GET /categories/{id}` | `abc` | **422** (id must be a number) |
| `PUT /categories/{id}` | `99` with `{"name": "Z"}` | **404** |
| `PUT /categories/{id}` | `2` with `{"name": "Microscopes"}` | **409** (name already used by category 1) |
| `DELETE /categories/{id}` | `99` | **404** |
| `DELETE /categories/{id}` | `1` | **409** "Category 1 is still used by other records and cannot be deleted" (it has equipment) |

#### Equipment

Use this body as the base: `{"name": "Test", "category_id": 1, "quantity_total": 1}`

| Request | Change | Expected |
|---|---|---|
| `POST /equipment` | `"category_id": 99` | **404** "Category 99 not found" |
| `POST /equipment` | `"quantity_total": 0` | **422** (must be at least 1) |
| `POST /equipment` | add `"quantity_available": 3` | **422** (stock is controlled by borrowing, not typed in) |
| `POST /equipment` | `"name": ""` | **422** |
| `GET /equipment/{id}` | `99` | **404** |
| `GET /equipment` | `limit` = `0` | **422** |
| `GET /equipment` | `limit` = `101` | **422** (the maximum is 100) |
| `PUT /equipment/{id}` | `99` with the base body | **404** |
| `DELETE /equipment/{id}` | `99` | **404** |

#### Borrowers

Use this body as the base: `{"full_name": "Someone", "borrower_type": "student", "id_number": "NEW-1"}`

| Request | Change | Expected |
|---|---|---|
| `POST /borrowers` | `"id_number": "2024-0001"` | **409** "A borrower with this id number already exists" |
| `POST /borrowers` | `"borrower_type": "teacher"` | **422** (only `student` or `faculty`) |
| `GET /borrowers/{id}` | `99` | **404** "Borrower 99 not found" |
| `GET /borrowers` | `borrower_type` = `teacher` | **422** |
| `PUT /borrowers/{id}` | `1` with `{"full_name": "Ana Cruz", "borrower_type": "student", "id_number": "EMP-0100"}` | **409** (that id number belongs to Prof. Reyes) |
| `DELETE /borrowers/{id}` | `99` | **404** |
| `DELETE /borrowers/{id}` | `1` | **409** (Ana has a loan on record) |

#### Loans

| Request | Body / parameter | Expected |
|---|---|---|
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 99}]}` | **409** "Not enough 'Compound microscope': requested 99, available 5" |
| `POST /loans` | `{"borrower_id": 99, "items": [{"equipment_id": 1, "quantity": 1}]}` | **404** "Borrower 99 not found" |
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 99, "quantity": 1}]}` | **404** "Equipment 99 not found" |
| `POST /loans` | `{"borrower_id": 2, "items": []}` | **422** (at least one item) |
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 1}, {"equipment_id": 1, "quantity": 1}]}` | **422** (same equipment twice) |
| `POST /loans` | `{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 0}]}` | **422** |
| `POST /loans` | `{"borrower_id": 2, "due_date": "2020-01-01", "items": [{"equipment_id": 1, "quantity": 1}]}` | **422** (due date in the past) |
| `POST /loans` | `{"borrower_id": 2, "due_date": "2099-01-01", "items": [{"equipment_id": 1, "quantity": 1}]}` | **422** (more than 14 days away) |
| `POST /loans/{id}/return` | `1` (already returned) | **409** "Loan 1 was already returned" |
| `POST /loans/{id}/return` | `99` | **404** |
| `GET /loans/{id}` | `99` | **404** "Loan 99 not found" |
| `GET /loans` | `status` = `lost` | **422** (only `active`, `overdue`, `returned`) |

---

### Part C: Rules that involve several tables

Run these after Part B, in order.

#### C1. A failed borrow is undone completely (transaction rollback)

`POST /loans`
```json
{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 1}, {"equipment_id": 2, "quantity": 99}]}
```
Expect **409** "Not enough 'HDMI cable 2m': requested 99, available 4".
The first item (1 microscope) was valid, but the whole borrow is all-or-nothing. Check: `GET /equipment/1` still shows `quantity_available` **5**, and `GET /loans` still lists only **1** loan.

#### C2. Make an active loan

`POST /loans`
```json
{"borrower_id": 2, "items": [{"equipment_id": 1, "quantity": 2}]}
```
Expect **201** with `"id": 2`. `GET /equipment/1` now shows `quantity_available` **3**.

#### C3. Units on loan are protected

- `PUT /equipment/1` with `{"name": "Compound microscope", "category_id": 1, "description": "40x to 1000x", "quantity_total": 1}` -> **409** "2 unit(s) are currently borrowed, so quantity_total cannot be lower than 2".
- `DELETE /equipment/1` -> **409** (this equipment appears in loans).

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

1. `GET /loans/2` -> **200** with `"status": "overdue"` and `"days_overdue": 3`. Also `GET /loans?status=overdue` -> lists loan 2.
2. `POST /loans` with `{"borrower_id": 2, "items": [{"equipment_id": 2, "quantity": 1}]}` -> **409**, because a borrower with an overdue loan cannot borrow again.
3. `POST /loans/2/return` -> **200** with `"status": "returned"`, `"days_overdue": 3` and `"penalty_amount": 5`.
   Borrower 2 is faculty: the first 2 late days are a grace period, then the rate is 5 pesos per day, so 3 days late costs 5. A **student** pays 10 pesos per late day from the first day (3 days late would cost 30).
4. Repeat the request from step 2 -> now **201**, because the overdue loan was returned.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | The virtual environment is not active. Activate it (2.2) and run `python -m pip install -r requirements.txt` again. |
| `No module named 'app'` or similar import errors | Run the server from the folder that contains `main.py`. |
| `Address already in use` | Another program uses port 8000. Run `python -m uvicorn main:app --reload --port 8001` and open `http://127.0.0.1:8001/docs`. |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. |
| The ids in the examples do not match | The database already has data. Stop the server, delete `equipment.db`, start again. |
| A 422 you did not expect | Open the response: the `detail` list names the field and the rule that failed. |