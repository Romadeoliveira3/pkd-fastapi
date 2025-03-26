from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import List
import httpx

oauth2_scheme = HTTPBearer()

KEYCLOAK_URL = "http://keycloak:8080"
REALM = "PKD-realm"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
ALGORITHM = "RS256"
AUDIENCE = "confidential-client"  # client_id registrado no Keycloak

class TokenData(BaseModel):
    username: str
    roles: List[str]

async def get_jwk():
    async with httpx.AsyncClient() as client:
        response = await client.get(JWKS_URL)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
        return response.json()

async def validate_token(token=Depends(oauth2_scheme)) -> TokenData:
    jwks = await get_jwk()
    unverified_header = jwt.get_unverified_header(token.credentials)

    key = next(
        (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]),
        None
    )

    if key is None:
        raise HTTPException(status_code=401, detail="Public key not found in JWKS")

    try:
        payload = jwt.decode(
            token.credentials,
            key,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            options={"verify_exp": True}
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    return TokenData(
        username=payload.get("preferred_username", "unknown"),
        roles=payload.get("realm_access", {}).get("roles", [])
    )
