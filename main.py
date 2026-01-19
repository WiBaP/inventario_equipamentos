from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from controllers.upload_controller import router as upload_router
from controllers.auth_controller import router as auth_router
from controllers.dispositivo_controller import router as dispositivo_router
from controllers.termos_controller import router as termos_router
from controllers.historico_controller import router as historico_router

app = FastAPI(
    title="Inventário de Dispositivos",
    version="1.0.0",
    description="API para gerenciar dispositivos."
)

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(upload_router)
app.include_router(termos_router)
app.include_router(historico_router)

# Templates
templates = Jinja2Templates(directory="templates")


# -----------------------------------------------------
# 1) MIDDLEWARE PARA PROTEGER TODAS AS PÁGINAS
# -----------------------------------------------------
@app.middleware("http")
async def verificar_login(request: Request, call_next):
    caminho = request.url.path

    #Rotas liberadas (não exigem estar logado)
    rotas_livres = ["/login", "/static", "/favicon.ico"]

     #Se começar com qualquer rota livre → libera
    if any(caminho.startswith(r) for r in rotas_livres):
        return await call_next(request)

     #Verificar cookie de sessão
    if not request.cookies.get("logado"):
        return RedirectResponse("/login")

    return await call_next(request)


# -----------------------------------------------------
# 2) ROTA PRINCIPAL → REDIRECIONA PARA LOGIN
# -----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse("/login")


# -----------------------------------------------------
# 3) ROTA DA SUA HOME (index.html)
# -----------------------------------------------------
@app.get("/index", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -----------------------------------------------------
# 4) REGISTRA CONTROLADORES
# -----------------------------------------------------
app.include_router(auth_router)
app.include_router(dispositivo_router)
