from fastapi import FastAPI,HTTPException
from pydantic import BaseModel

router = FastAPI()

class Product(BaseModel):
    id: str
    name: str
    price: str

product_db = [
    {
        "id":"1",
        "name":"aceite",
        "price":"700"
    },
    {
        "id":"2",
        "name":"cervesa",
        "price":"250"
    },
    {
        "id":"3",
        "name":"detergente",
        "price":"600"
    },
    {
        "id":"4",
        "name":"refresco",
        "price":"300"
    },
    {
        "id":"5",
        "name":"cemento",
        "price":"5000"
    },
]


@router.get("/",response_model = list[Product])
def get_products():
    return product_db

@router.get("/{product_name}",response_model = Product)
def get_products(product_name: str):
    for product in product_db:
        if product["name"] == product_name:
            return product
    return HTTPException(status_code=404,detail="Product not found")

@router.post("/",response_model=Product)
def create_product(product_data:Product):
    new_product = product_data.model_dump() 
    product_db.append(new_product)
    return new_product

@router.delete("/{product_name}",response_model=Product)
def delete_product(product_id:str):
    for product in product_db:
        if product["id"]==product_id:
            product_db.remove(product)
            return product
    return HTTPException(status_code=404,detail="Product not found")