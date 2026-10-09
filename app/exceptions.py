"""Domain errors raised by the repositories and services.
 
They know nothing about HTTP. main.py maps them to status codes, so the
database and business code stay independent of FastAPI.
"""

class NotFoundError(Exception):
      """A requested record does not exist (becomes HTTP 404)."""
class ConflictError(Exception):
    """The request conflics with the current data (becomes HTTP 409)."""