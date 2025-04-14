from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from typing import List
import httpx

oauth2_scheme = HTTPBearer()

NGINX_INTROSPECT_URL = "http://nginx-gateway/auth/introspect"
KEYCLOAK_CLIENT_ID = "confidential-client"
KEYCLOAK_CLIENT_SECRET = "PKD-client-secret"

class TokenData(BaseModel):
    username: str
    roles: List[str]
    token: str

async def validate_token_introspect(token: str) -> TokenData:
    token = token.replace("Bearer ", "")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": token,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET
    }

    print("Enviando introspect via NGINX:")
    print(f"token: {token[:40]}...")
    print(f"url: {NGINX_INTROSPECT_URL}")

    async with httpx.AsyncClient() as client:
        response = await client.post(NGINX_INTROSPECT_URL, headers=headers, data=data)
        print(f"Status introspect: {response.status_code}")
        print(f"Resposta introspect: {response.text}")

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Falha na introspecção com Keycloak via NGINX")

        result = response.json()
        if not result.get("active", False):
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    return TokenData(
        username=result.get("preferred_username", "desconhecido"),
        roles=result.get("realm_access", {}).get("roles", []),
        token=token
    )

async def validate_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    if not token or not token.credentials:
        raise HTTPException(status_code=401, detail="Token de acesso ausente")
    return await validate_token_introspect(token.credentials)
