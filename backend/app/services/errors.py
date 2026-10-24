"""Domain errors. Services raise these; the API layer maps them to HTTP responses."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class AuthError(DomainError):
    status_code = 401


class ForbiddenError(DomainError):
    status_code = 403
