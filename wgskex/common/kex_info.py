import re
from typing import Optional

from pydantic import BaseModel, validator

WG_PUBKEY_PATTERN = re.compile(r"^[A-Za-z0-9+/]{42}[AEIMQUYcgkosw480]=$")


class KexInfo(BaseModel):
    domain: str
    public_key: str

    @validator("public_key")
    def validate_public_key(cls, value: str) -> str:
        if not WG_PUBKEY_PATTERN.match(value):
            raise ValueError("public_key must be a valid WireGuard public key")
        return value


class KexResult(BaseModel):
    status: str
    message: Optional[str] = None

    @validator("status")
    def validate_status(cls, value: str) -> str:
        if value not in ["OK", "error"]:
            raise ValueError("")
        return value
