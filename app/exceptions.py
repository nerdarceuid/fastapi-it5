class NotFoundError(Exception):
      """A requested record does not exist (becomes HTTP 404)."""
class ConflictError(Exception):
      """The request conflics with the current data (becomes HTTP 409)."""

class InsufficientStockError(ConflictError):
      """ Not enough units of an equipment item are available -> 409"""