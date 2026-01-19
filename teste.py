import os
PASTA_TERMOS = r"C:\Users\willian.pinho\Desktop\notebooksteste\termos"
usuario = "marcelo.filho"
print(os.path.isfile(os.path.join(PASTA_TERMOS, f"{usuario}.pdf")))
