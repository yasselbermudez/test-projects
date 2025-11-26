from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio
from typing import Optional
import uuid
#pip install playwright
#playwright install chromium
#playwright install firefox
#playwright install webkit
app = FastAPI()

# Almacenamiento temporal de sesiones
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class DeepSeekScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    async def initialize(self):
        """Inicializa el navegador"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
        # Navegar a DeepSeek chat
        await self.page.goto('https://chat.deepseek.com/', wait_until='networkidle')
        await asyncio.sleep(2)
    
    async def send_message(self, message: str) -> str:
        """Envía un mensaje y obtiene la respuesta"""
        try:
            # Buscar el textarea o input del chat
            # Nota: Los selectores pueden cambiar, necesitas inspeccionar la página
            textarea = await self.page.wait_for_selector(
                'textarea, input[type="text"]',
                timeout=10000
            )
            
            # Escribir el mensaje
            await textarea.fill(message)
            await asyncio.sleep(0.5)
            
            # Presionar Enter o buscar botón de envío
            await textarea.press('Enter')
            
            # Esperar la respuesta (ajusta el selector según la estructura HTML)
            await asyncio.sleep(2)
            
            # Obtener la última respuesta del chat
            # Este selector es genérico, necesitas ajustarlo según DeepSeek
            response = await self.page.wait_for_selector(
                '.message.assistant:last-child, .response:last-child',
                timeout=30000
            )
            
            response_text = await response.inner_text()
            return response_text
            
        except Exception as e:
            raise Exception(f"Error al obtener respuesta: {str(e)}")
    
    async def close(self):
        """Cierra el navegador"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

@app.on_event("startup")
async def startup_event():
    """Inicializa recursos al arrancar"""
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Limpia recursos al cerrar"""
    for session in sessions.values():
        await session.close()

@app.post("/chat/scrape", response_model=ChatResponse)
async def chat_scrape(request: ChatRequest):
    """
    Endpoint para chatear con DeepSeek mediante scraping
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Crear o reutilizar sesión
        if session_id not in sessions:
            scraper = DeepSeekScraper()
            await scraper.initialize()
            sessions[session_id] = scraper
        else:
            scraper = sessions[session_id]
        
        # Enviar mensaje y obtener respuesta
        response_text = await scraper.send_message(request.message)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id
        )
        
    except Exception as e:
        # Limpiar sesión en caso de error
        if session_id in sessions:
            await sessions[session_id].close()
            del sessions[session_id]
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/session/{session_id}")
async def close_session(session_id: str):
    """Cierra una sesión de scraping"""
    if session_id in sessions:
        await sessions[session_id].close()
        del sessions[session_id]
        return {"message": "Sesión cerrada"}
    raise HTTPException(status_code=404, detail="Sesión no encontrada")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)