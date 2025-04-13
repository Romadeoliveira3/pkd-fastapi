from fastapi import APIRouter, Depends, HTTPException
from auth import validate_token, TokenData
from pydantic import BaseModel, EmailStr
import httpx
import os

user_router = APIRouter(tags=["User"])

KEYCLOAK_SERVER_URL = "http://keycloak:8080"
REALM_NAME = "PKD-realm"
CLIENT_ID = "confidential-client"
CLIENT_SECRET = "PKD-client-secret"

# Modelo de entrada do usuário
class NovoUsuario(BaseModel):
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    enabled: bool = True


# Obter token admin via client credentials
async def get_admin_token():
    url = f"{KEYCLOAK_SERVER_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise HTTPException(status_code=500, detail="Erro ao obter token admin do Keycloak.")

# Rota protegida para criação de usuários no Keycloak
@user_router.post("/signup", summary="Criar novo usuário no Keycloak")
async def user_signup(
    user: NovoUsuario,
    current_user: TokenData = Depends(validate_token)
):
    token = await get_admin_token()
    url = f"{KEYCLOAK_SERVER_URL}/admin/realms/{REALM_NAME}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=user.dict())

    if response.status_code == 201:
        return {"message": "Usuário criado com sucesso!"}
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Usuário já existe.")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)