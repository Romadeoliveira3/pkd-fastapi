from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from keycloak import KeycloakOpenID

# Configuração do Keycloak
KEYCLOAK_SERVER_URL = "http://localhost:8080"
REALM_NAME = "PKD-realm"
CLIENT_ID = "PKD-client"
CLIENT_SECRET = "PKD-clientsecret"  # Pegue isso no Keycloak se for confidential

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_SERVER_URL,
    client_id=CLIENT_ID,
    realm_name=REALM_NAME,
    client_secret_key=CLIENT_SECRET,
)

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(request: LoginRequest):
    try:
        token = keycloak_openid.token(request.username, request.password)
        return {"access_token": token["access_token"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

def get_current_user(token: str = Depends(keycloak_openid.decode_token)):
    try:
        return token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return {"message": "You have access!", "user": user}