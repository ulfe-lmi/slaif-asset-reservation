from __future__ import annotations


class ApiTokenDomainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


TOKEN_OWNER_INVALID = "token_owner_invalid"
TOKEN_SCOPE_INVALID = "token_scope_invalid"
TOKEN_LIFETIME_INVALID = "token_lifetime_invalid"
TOKEN_NOT_OWNED = "token_not_owned"
