"""In-memory repository.

Deliberately exposes **no update/delete for raw facts** (``PriceBar`` /
``FundamentalSnapshot``): corrections are appended as new versions. This encodes
the ``NO_RAW_MUTATION`` invariant at the storage boundary. Swap this module for a
SQLAlchemy-backed implementation without changing callers.
"""

from app.repository.memory import Repository, repo

__all__ = ["Repository", "repo"]
