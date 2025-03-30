from pymongo import MongoClient

def connect_to_db():
    try:
        client = MongoClient("mongodb://localhost:27017/")  # Ajusta si usas otro host/puerto
        db = client['bmw_concesionario']
        print("Conexión con MongoDB establecida")
        return db
    except Exception as e:
        print("Error al conectar con MongoDB:", e)  # Imprime el error si la conexión falla
        return None