from fastapi import FastAPI
from chipsets import chipsets_router
from user import user_router
# from microservice_chipset.chipsets import chipsets_router
# from microservice_chipset.user import user_router



app = FastAPI(
    title="Microserviço Central",
    root_path="/chipsets",
    version="1.0.0",
    description="Gerencia chipsets e usuários"
)


app.include_router(chipsets_router)
app.include_router(user_router)
