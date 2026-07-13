from typing import Any, Iterable


def sanitize_validation_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove input e contexto potencialmente sensiveis de erros Pydantic."""
    return [
        {
            key: value
            for key, value in error.items()
            if key in {"type", "loc", "msg"}
        }
        for error in errors
    ]
