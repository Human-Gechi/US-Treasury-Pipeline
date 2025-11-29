import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from Data.models

load_dotenv()


app = FastAPI(
    title="US treasury data",
    version="1.0.0",
    description="Application Interface Programming for Average rate of US securities"
)

# Enable CORS for local & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Average Rate US Treasury API is running"}

@app.get("/records/")
async def all_records():

#FastAPi doc
# from typing import Annotated

# from fastapi import Body, FastAPI
# from pydantic import BaseModel, Field

# app = FastAPI()


# class Item(BaseModel):
#     name: str
#     description: str | None = Field(
#         default=None, title="The description of the item", max_length=300
#     )
#     price: float = Field(gt=0, description="The price must be greater than zero")
#     tax: float | None = None


# @app.put("/items/{item_id}")
# async def update_item(item_id: int, item: Annotated[Item, Body(embed=True)]):
#     results = {"item_id": item_id, "item": item}
#     return results