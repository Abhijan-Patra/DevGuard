from cart import cart_total
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class Item(BaseModel):
    unit_amount: int = Field(ge=0, le=1_000_000)
    quantity: int = Field(ge=1, le=1000)


class Cart(BaseModel):
    items: list[Item] | None = None


@app.post("/cart/total")
def total(cart: Cart):
    return {
        "total_minor": cart_total(
            None if cart.items is None else [i.model_dump() for i in cart.items]
        )
    }
