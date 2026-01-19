import os
from fastapi import UploadFile

class UploadService:
    def __init__(self):
        # Caminho onde os PDFs ficarão armazenados
        self.PASTA_TERMOS = r"C:\Users\willian.pinho\Desktop\termos"
        os.makedirs(self.PASTA_TERMOS, exist_ok=True)

    async def salvar_termo(self, usuario: str, file: UploadFile):
        """Salva o PDF com o nome do usuário."""
        nome_arquivo = f"{usuario}.pdf"
        caminho = os.path.join(self.PASTA_TERMOS, nome_arquivo)

        with open(caminho, "wb") as f:
            f.write(await file.read())

        return caminho
