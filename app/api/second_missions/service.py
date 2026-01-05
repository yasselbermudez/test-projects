from datetime import datetime
import json
import re

from fastapi import HTTPException,status
from .schemas import MissionApi, SecondaryMission
from app.database.database import prepare_for_mongo
from app.core.config import settings
from google import genai
from typing import Optional

import logging
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

async def create_secondary_mission(user_id:str,db,instruction:Optional[str]=None) -> SecondaryMission:
    try:
        logger.info(f"creating a secondary mission for the user: {str(user_id)}")
        profile = await db.profiles.find_one(
            {"user_id": user_id},
            {   
                "name": 1, "apodo": 1, "peso_corporal": 1,
                "altura": 1, "pesos": 1, "objetivo": 1, "_id": 0
            }
        )
    
        if not profile:
            logger.error("Profile not found")
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Profile not found")
        
        resumen = await db.summary.find_one(
            {"user_id": user_id},
            {"perfil_sintetizado": 1, "_id": 0}
        )
        
        history = await db.history.find(
            {"user_id": user_id},
            {"tipo": 1, "description": 1, "result": 1, "_id": 0}
        ).to_list(100)

        if not instruction:
            instruction = """Eres un asistente que genera retos semanales personalizados para un grupo de amigos que se motivan en un juego donde cumplen retos y misiones
                Genera un reto para una persona con las siguientes instrucciones:
                El reto debe ser:
                - CONCISO, con un ÚNICO OBJETIVO PRINCIPAL y ACCIONES DIRECTAS. 
                - Relacionado con gym,amistad,relaciones,retos alocados,hacer el ridiculo,emprendimiento y superacion personal
                - Realista y alcanzable en 1 semana,no debe ser muy complicado de realizar 
                - Personalizado según su historial,resumen y perfil """

        # Build the prompt
        prompt = f"""
        {instruction}
        Tendras la siguiente informacion de la persona:
        - Perfil: {profile}
        - Resumen: {resumen}
        - Historial de retos: {history[-3:] if history else 'Sin historial'}
        
        IMPORTANTE: Responde SOLO con un JSON válido con esta estructura exacta:
        {{
            "nombre": "nombre corto de el reto",
            "descripcion": "descripción concisa maximo 200 palabras",
            "recompensa": "un string con la cantidad de recompensa entre 100 y 1000"
        }}
        """

        # Call Google Gemini API
        try:
            response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
            )
        except Exception as e:
            logger.error(f"Error calling the Gemini API.: {str(e)}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,detail="Error calling the Gemini API.")

        # Procesar la respuesta
        if not response.text:
            logger.error("Gemini API response is empty")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,detail="Gemini API response is empty.")

        mission_content = response.text
        
        # Clean and parse the JSON
        try:
            # Parse directly
            mission_dict = json.loads(mission_content)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the text
            json_match = re.search(r'\{[^{}]*\}', mission_content.strip())
            if json_match:
                try:
                    mission_dict = json.loads(json_match.group())
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to extract valid JSON from the response: {str(e)}")
                    raise ValueError(f"Failed to extract valid JSON from the response: {str(e)}")
            else:
                logger.error("No JSON found in the response")
                raise ValueError("No JSON found in the response")
        
        
        try:
            # Manually map the JSON and validate
            mission_api_obj = MissionApi (
                nombre= mission_dict.get("nombre", ""),
                descripcion= mission_dict.get("descripcion", ""),
                recompensa= mission_dict.get("recompensa", "100XP") 
            )

            mission_obj = SecondaryMission(
                user_id= user_id,
                nombre= mission_api_obj.nombre,
                descripcion= mission_api_obj.descripcion,
                recompensa= mission_api_obj.recompensa,
                created= datetime.now(),
                is_active= True
            )

        except Exception as e:
            logger.error(f"Error validating mission data.: {str(e)}"),
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Error validating mission data.")
            
        response = await db.secondary.insert_one(prepare_for_mongo(mission_obj.dict()))
        logger.info(f"Secondary mission created successfully with id: {str(response.inserted_id)}")
        return mission_obj
    
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating secundary mission : {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error generating secundary mission : {str(e)}")
