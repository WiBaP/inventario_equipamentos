from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from service.ad_auth_service import ADAuthService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configuração do AD
ad_service = ADAuthService(
    server_url="ldap://DC01.seudominio.local",
    domain="SEUDOMINIO"
)

# ====== USUÁRIOS AUTORIZADOS ======
USUARIOS_AUTORIZADOS = {
    "willian.pinho",
    "weslley.nascimento",
    "guilherme.azevedo",
    "thiago.porto",
    "william.silva",
    "caroline.g"
}
# ==================================


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request,
                username: str = Form(...),
                password: str = Form(...)):

    # 1️⃣ Verificar se está na lista de autorizados
    if username not in USUARIOS_AUTORIZADOS:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "erro": "Usuário não autorizado a acessar o sistema."}
        )

    # 2️⃣ Autenticar no AD
    ad_user = ad_service.authenticate(username, password)

    if not ad_user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "erro": "Usuário ou senha inválidos"}
        )

    # 3️⃣ Criar cookies de sessão
    response = RedirectResponse(url="/index", status_code=302)
    response.set_cookie("logado", "1")
    response.set_cookie("usuario", ad_user["username"])
    response.set_cookie("nome", ad_user["nome"])
    response.set_cookie("email", ad_user["email"])

    return response
