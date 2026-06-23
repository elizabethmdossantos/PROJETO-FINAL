import mysql.connector
from mysql.connector import Error

def obter_conexao():
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="sistema_gestao_empresa"
        )
        if conexao.is_connected():
            return conexao
    except Error as e:
        print(f"Erro ao conectar ao Mysql: {e}")
        return None