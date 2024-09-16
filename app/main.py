from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
import database
from api import admin, login, sales, customer, accounts
from dotenv import load_dotenv


load_dotenv()
app = FastAPI()



origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


models.Base.metadata.create_all(bind=database.engine)

app.include_router(admin.router)
app.include_router(login.router)
app.include_router(sales.router)
app.include_router(customer.router)
app.include_router(accounts.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}