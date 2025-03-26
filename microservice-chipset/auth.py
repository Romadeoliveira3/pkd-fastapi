from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import List
import httpx

oauth2_scheme = HTTPBearer()

KEYCLOAK_URL = "http://keycloak:8080"
REALM_NAME = "PKD-realm"
INTROSPECT_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token/introspect"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/certs"
ALGORITHM = "RS256"
KEYCLOAK_CLIENT_ID = "confidential-client"
KEYCLOAK_CLIENT_SECRET = "PKD-client-secret"

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    username: str
    roles: List[str]


async def validate_token_introspect(token: str) -> TokenData:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": token,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(INTROSPECT_URL, headers=headers, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Keycloak introspection failed")
        result = response.json()
        if not result.get("active", False):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    return TokenData(
        username=result.get("preferred_username", "unknown"),
        roles=result.get("realm_access", {}).get("roles", [])
    )

async def validate_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Missing access token")
    return await validate_token_introspect(token.credentials)


# async def get_jwk():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(JWKS_URL)
#         if response.status_code != 200:
#             raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
#         return response.json()

# async def validate_token(token=Depends(oauth2_scheme)) -> TokenData:
#     jwks = await get_jwk()
#     unverified_header = jwt.get_unverified_header(token.credentials)

#     key = next(
#         (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]),
#         None
#     )

#     if key is None:
#         raise HTTPException(status_code=401, detail="Public key not found in JWKS")

#     try:
#         payload = jwt.decode(
#             token.credentials,
#             key,
#             algorithms=[ALGORITHM],
#             audience=AUDIENCE,
#             options={"verify_exp": True}
#         )
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Token inválido ou expirado")

#     return TokenData(
#         username=payload.get("preferred_username", "unknown"),
#         roles=payload.get("realm_access", {}).get("roles", [])
#     )

