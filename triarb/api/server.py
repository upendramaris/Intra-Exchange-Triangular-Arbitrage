from fastapi import FastAPI

from triarb.api.routes import router

app = FastAPI(title="Triangular Arbitrage Admin")
app.include_router(router)
