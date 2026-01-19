import pyodbc

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=PDVHMG003-001\SQLEXPRESS;"
        "DATABASE=inventario;"
        "Trusted_Connection=yes;"
    )
