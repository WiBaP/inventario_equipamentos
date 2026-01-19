# 📦 Sistema de Inventário e Automação de TI

⚠️ **Dependência obrigatória:**  
Este projeto **depende diretamente** do repositório **usuarios_ad.git**, que é responsável pela integração e sincronização com o Active Directory.  
Ele deve estar configurado e funcionando antes da execução deste sistema.

> Repositório: https://github.com/WiBaP/usuarios_ad.git

Sistema desenvolvido em Python para gerenciamento de equipamentos, usuários e automações integradas ao Active Directory.

O projeto tem como objetivo centralizar o controle de inventário, histórico de movimentações e rotinas administrativas, reduzindo atividades manuais do setor de TI.

---

## 🚀 Funcionalidades

- Autenticação integrada ao Active Directory  
- Cadastro e gerenciamento de equipamentos  
- Controle de dispositivos  
- Histórico de movimentações  
- Upload de arquivos  
- Integração com banco de dados  
- Rotinas de automação administrativa  

---

## 🛠 Tecnologias utilizadas

- Python  
- FastAPI  
- SQL Server  
- PyODBC  
- HTML / CSS / JavaScript  
- Active Directory  

---

## ⚙️ Como instalar o projeto

```bash
git clone https://github.com/WiBaP/inventario_equipamentos.git
cd inventario_equipamentos.git
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

▶️ Como executar
uvicorn main:app --reload

Acesse:
http://localhost:8000

🗂 Estrutura do projeto
cpp
Copiar código
├── auth
├── controllers
├── db
├── model
├── service
├── static
├── templates
├── main.py

📌 Observações
O sistema utiliza autenticação via Active Directory

As strings de conexão e credenciais devem ser definidas via variáveis de ambiente

Este projeto está em desenvolvimento contínuo

🔮 Próximas implementações
Painel administrativo

Controle de permissões

Logs centralizados

Dashboard de indicadores

Automatizações avançadas de AD
