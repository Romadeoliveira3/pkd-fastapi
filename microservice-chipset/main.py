from fastapi import FastAPI, Depends
from auth import validate_token, TokenData

app = FastAPI(
    root_path="/chipsets",
    title="Chipset Microservice",
    version="1.0.0",
    description="API responsável pelo gerenciamento de chipsets disponíveis no sistema."
)

@app.get("/", summary="List Chipsets", tags=["Chipsets"])
async def list_chipsets(current_user: TokenData = Depends(validate_token)):
    return [
        {"model": "ESP32", "manufacturer": "Espressif"},
        {"model": "STM32", "manufacturer": "STMicroelectronics"},
        {"model": "ATmega328", "manufacturer": "Microchip"}
    ]

@app.get("/public", summary="Public Endpoint", tags=["Public"])
async def public_chipsets():
    return {"message": "Este é um endpoint público do microserviço de chipsets."}
