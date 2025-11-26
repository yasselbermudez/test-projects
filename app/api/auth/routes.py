from fastapi import APIRouter, Cookie, Depends, Request, status, Response
from .schemas import UserCreate, UserLogin, Token, User
from . import service
from app.database.database import get_database

router = APIRouter()

TOKEN_SECONDS_EXP = 900  # 15 min

@router.post("/register",status_code=status.HTTP_201_CREATED,response_model=User)
async def register_user(user_data: UserCreate, response:Response, db=Depends(get_database)):
    result =  await service.create_user(user_data,db)
    token = result.get("access_token")
    user= result.get("user")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,   # poner True en producción (HTTPS)
        samesite="lax",
        max_age=TOKEN_SECONDS_EXP,
        path="/",
    )
    return user 

@router.post("/login", response_model=User)
async def login_user(login_data: UserLogin,response: Response, db=Depends(get_database)):
    result = await service.authenticate_user(login_data,db)
    user = result.get("user")
    token = result.get("access_token")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False, # poner True en producción (HTTPS)
        samesite="lax",
        max_age=TOKEN_SECONDS_EXP,
        path="/"
        )
    # Opcional: crear y devolver un CSRF token que el cliente debe enviar en headers
    # csrf_token = generate_csrf()  # función que genere token aleatorio
    # response.set_cookie("csrf_token", csrf_token, httponly=False, secure=False, samesite="lax")
    return user

@router.post("/logout", status_code=204)
async def logout(response: Response):
    # Borra la cookie en el cliente
    response.delete_cookie("access_token", path="/")
    # si tienes csrf cookie: response.delete_cookie("csrf_token", path="/")
    return Response(status_code=204)

#@router.post("/refresh", response_model=User)



