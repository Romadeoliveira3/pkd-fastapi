from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import httpx
from auth import validate_token, TokenData

user_router = APIRouter(tags=["User"])

KEYCLOAK_CREATE_USER_URL = "http://nginx-gateway/auth/admin/realms/PKD-realm/users"

class NovoUsuario(BaseModel):
    username: str
    email: EmailStr
    firstName: str
    lastName: str
    password: str
    temporary: bool = False
    enabled: bool = True
    emailVerified: bool = True

    @property
    def credentials(self) -> list[dict]:
        return [{
            "type": "password",
            "value": self.password,
            "temporary": self.temporary
        }]


@user_router.get("/login", summary="Obter token de acesso do Keycloak")
async def get_token(
    username: str,
    password: str
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://nginx-gateway/auth/token",
            data={
                "client_id": "confidential-client",
                "client_secret": "PKD-client-secret",
                "username": username,
                "password": password,
                "grant_type": "password",
                "scope": "openid"
            }
        )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

@user_router.post("/signup", summary="Criar novo usuário no Keycloak via NGINX")
async def user_signup(
    user: NovoUsuario,
    current_user: TokenData = Depends(validate_token)
):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {current_user.token}"  
    }

    user_payload = {
        "username": user.username,
        "email": user.email,
        "enabled": user.enabled,
        "firstName": user.firstName,
        "lastName": user.lastName,
        "credentials": user.credentials,
        "emailVerified": user.emailVerified
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(KEYCLOAK_CREATE_USER_URL, headers=headers, json=user_payload)

    if response.status_code == 201:
        return {"message": "Usuário criado com sucesso!"}
    elif response.status_code == 409:
        raise HTTPException(status_code=409, detail="Usuário já existe.")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
