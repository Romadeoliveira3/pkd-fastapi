import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from unittest.mock import AsyncMock, patch

from main import app
from auth import TokenData

# Mock de dados de entrada
mock_user_data = {
    "username": "usuario_teste",
    "email": "teste@example.com",
    "firstName": "Teste",
    "lastName": "Usuário",
    "enabled": True
}

# Mock de token válido
mock_token_data = TokenData(
    username="admin",
    roles=["admin"],
    token="fake-token"
)

@pytest.mark.asyncio
async def test_user_signup_success():
    """
    Testa criação de usuário com sucesso (status 201 do Keycloak).
    """
    mock_post = AsyncMock()
    mock_post.return_value.status_code = 201

    with patch("auth.validate_token", return_value=mock_token_data), \
         patch("httpx.AsyncClient.post", new=mock_post):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/signup",
                json=mock_user_data,
                headers={"Authorization": "Bearer fake-token"}
            )

        assert response.status_code == 201
        # opcional: verificar response.json() se você padronizar retorno

@pytest.mark.asyncio
async def test_user_signup_user_exists():
    """
    Testa tentativa de criação de usuário já existente (status 409).
    """
    mock_post = AsyncMock()
    mock_post.return_value.status_code = 409
    mock_post.return_value.json = AsyncMock(return_value={"detail": "Usuário já existe."})

    with patch("auth.validate_token", return_value=mock_token_data), \
         patch("httpx.AsyncClient.post", new=mock_post):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/signup",
                json=mock_user_data,
                headers={"Authorization": "Bearer fake-token"}
            )

        assert response.status_code == status.HTTP_409_CONFLICT
        json_response = await response.json()
        assert json_response["detail"] == "Usuário já existe."

@pytest.mark.asyncio
async def test_user_signup_keycloak_error():
    """
    Testa erro genérico vindo do Keycloak (status 500).
    """
    mock_post = AsyncMock()
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Erro interno no Keycloak"
    mock_post.return_value.json = AsyncMock(return_value={"detail": "Erro interno no Keycloak"})

    with patch("auth.validate_token", return_value=mock_token_data), \
         patch("httpx.AsyncClient.post", new=mock_post):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/signup",
                json=mock_user_data,
                headers={"Authorization": "Bearer fake-token"}
            )

        assert response.status_code == 500
        json_response = await response.json()
        assert "Erro interno no Keycloak" in json_response["detail"]
