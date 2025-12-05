from datetime import datetime
import json
import re
from .schemas import EventResponse, MissionApi, SecondaryMission
from app.database.database import prepare_for_mongo
from app.core.config import settings
from google import genai

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
client = genai.Client(api_key=settings.GOOGLE_API_KEY)


async def create_secondary_mission(user_id, db) -> EventResponse:
    try:
        # Obtener datos del usuario
        perfil = await db.profiles.find_one(
            {"user_id": user_id},
            {   
                "name": 1, "apodo": 1, "peso_corporal": 1,
                "altura": 1, "pesos": 1, "objetivo": 1, "_id": 0
            }
        )
        
        # Verificar que se encontró el perfil
        if not perfil:
            return EventResponse(
                id="",
                message="No se encontró el perfil del usuario",
                success=False,
                mission_id="",
                mission_name=""
            )
        
        resumen = await db.summary.find_one(
            {"user_id": user_id},
            {"perfil_sintetizado": 1, "_id": 0}
        )
        
        history = await db.history.find(
            {"user_id": user_id},
            {"tipo": 1, "description": 1, "result": 1, "_id": 0}
        ).to_list(100)

        # Construir el prompt
        prompt = f"""
        Eres un asistente que genera retos semanales personalizados para un grupo de amigos que se motivan en un juego donde cumplen retos y misiones
        Genera un reto para una persona con las siguientes instrucciones:
        El reto debe ser:
        - CONCISO, con un ÚNICO OBJETIVO PRINCIPAL y ACCIONES DIRECTAS. 
        - Divertido, realista y relacionado con gym,amistad,relaciones y superacion personal
        - Alcanzable en 1 semana,no debe ser muy complicado de realizar 
        - Personalizado según su historial,resumen y perfil

        Tendras la siguiente informacion de la persona:
        - Perfil: {perfil}
        - Resumen: {resumen}
        - Historial de retos: {history[-3:] if history else 'Sin historial'}
        
        IMPORTANTE: Responde SOLO con un JSON válido con esta estructura exacta:
        {{
            "nombre": "nombre corto de el reto",
            "descripcion": "descripción concisa maximo 200 palabras",
            "recompensa": "un string con la cantidad de recompensa entre 100 y 1000"
        }}
        """

        # Llamar a la API de Google Gemini
        response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
        )

        # Procesar la respuesta
        if not response.text:
            return EventResponse(
                id="",
                message="Error: Respuesta vacía de gemini",
                success=False,
                mission_id="",
                mission_name=""
            )
        mission_content = response.text
        
        # Limpiar y parsear el JSON
        try:
            # Intentar parsear directamente
            mission_dict = json.loads(mission_content)
        except json.JSONDecodeError as e:
            # Si falla, intentar extraer JSON del texto
            json_match = re.search(r'\{[^{}]*\}', mission_content.strip())
            if json_match:
                try:
                    mission_dict = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError("No se pudo extraer JSON válido de la respuesta")
            else:
                raise ValueError("No se encontró JSON en la respuesta")
        
        # Mapear manualmente los campos
        mission_data = {
            "nombre": mission_dict.get("nombre", ""),
            "descripcion": mission_dict.get("descripcion", ""),
            "recompensa": mission_dict.get("recompensa", "100XP") 
        }
        
        # Validar con Pydantic
        try:
            mission_api_obj = MissionApi(**mission_data)
        except Exception as e:
            return EventResponse(
                id="",
                message=f"Error validando datos de la misión: {str(e)}",
                success=False,
                mission_id="",
                mission_name=""
            )
        
        # Preparar documento para MongoDB
        mission_doc = {
            "user_id": user_id,
            "nombre": mission_api_obj.nombre,
            "descripcion": mission_api_obj.descripcion,
            "recompensa": mission_api_obj.recompensa,
            "created": datetime.now(),
            "is_active": True
        }

        mission_obj = SecondaryMission(**mission_doc)
        
        # Insertar en MongoDB
        response = await db.secondary.insert_one(prepare_for_mongo(mission_obj.dict()))
        
        return EventResponse(
            message="Mission create succes OK",
            mission_id=mission_obj.id,
            mission_name=mission_obj.nombre,
            success=True
        )
        
    except Exception as e:
        return EventResponse(
            message=f"Error en API de gemini: {str(e)}",
            success=False,
            mission_id="",
            mission_name=""
        )











    
#prompt original
"""
prompt = {
            "model": "deepseek-chat",  # modelo no pensante , deepseek-reasoner -> para modelo pensante
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente creativo que genera misiones secundarias divertidas y alcanzables para un grupo de amigos que documentan sus experiencias en el gimnasio y póker."
                },
                {
                    "role": "user", 
                    "content": f"
                    Somos un grupo de 5 amigos documentando nuestras aventuras en el gym y el póker. 
                    Genera una misión secundaria creativa y personalizada para esta persona.
                    
                    PERFIL DEL JUGADOR:
                    - Perfil: {perfil}
                    - Resumen: {resumen}
                    - Historial de misiones: {history}
                    
                    La misión debe ser:
                    - Divertida y relacionada con gym/póker/amistad
                    - Alcanzable en 1 semana
                    - Personalizada según su historial y perfil
                    - Incluir objetivos claros y recompensa en el rango de 100XP-1000XP
                    
                    Formato de respuesta: JSON con 'nombre', 'descripcion', 'objetivos', 'dificultad', 'recompensa'
                    "
                }
            ],
            "max_tokens": 1000
        }
"""