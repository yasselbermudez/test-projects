from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from .schemas import UserCreate, UserLogin, User
from . import service
from app.database.database import get_database
import logging

logger = logging.getLogger("auth.routes")

router = APIRouter()

secure = True  # Cambiar a True en producción (HTTPS)

REFRESH_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS*24*60*60
ACCESS_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES*60

@router.post("/register",status_code=status.HTTP_201_CREATED,response_model=User)
async def register_user(user_data: UserCreate, response:Response, db=Depends(get_database)):
    
    user =  await service.create_user(user_data,db)
   
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    response.set_cookie(
        key="access_token",            
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=ACCESS_MAX_AGE,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=REFRESH_MAX_AGE,
        path="/"
    )
    return user 

@router.post("/login",response_model=User)
async def login_user(login_data: UserLogin,response: Response, db=Depends(get_database)):
    
    logger.info(f"Attempting login for user: {login_data.email}")
        
    user = await service.authenticate_user(login_data,db)
        
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
        
    await service.save_refresh_token_to_db(user.id, refresh_token, db)
        
    response.set_cookie(
        key="access_token",            
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=ACCESS_MAX_AGE,
        path="/"
    )
        
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=REFRESH_MAX_AGE,
        path="/"
    )

    # Opcional: crear y devolver un CSRF token que el cliente debe enviar en headers
    # csrf_token = generate_csrf()  # función que genere token aleatorio
    # response.set_cookie("csrf_token", csrf_token, httponly=False, secure=False, samesite="lax")
    return user
    
@router.post("/refresh", response_model=User)
async def refresh_token(response: Response,request:Request, db=Depends(get_database)):
    
    user = await service.refresh_access_token(request,db)
    
    new_access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    await service.save_refresh_token_to_db(user.id, new_refresh_token, db)

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=secure,  
        samesite="lax",
        max_age=ACCESS_MAX_AGE,
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=secure, 
        samesite="lax",
        max_age=REFRESH_MAX_AGE,
        path="/"
    )
    return user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db=Depends(get_database)):
    
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        try:
            await service.revoke_refresh_token(refresh_token, db)
        except:
            pass

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    # si tienes csrf cookie: response.delete_cookie("csrf_token", path="/")
    return Response(status_code=204)



