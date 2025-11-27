# seed.py
from pymongo import MongoClient
from datetime import datetime
import os

# Crear cliente MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.farmacia

# Datos de ejemplo para productos
products = []

# Usuario administrador de ejemplo
users = [
    {
        'email': 'admin@farmacia.com',
        'password': 'admin123',  # En producción usar hashing!
        'role': 'admin',
        'created_at': datetime.utcnow()
    },
    {
        'email': 'cliente@ejemplo.com', 
        'password': 'cliente123',
        'role': 'user',
        'created_at': datetime.utcnow()
    }
]

def seed_database():
    print("🧹 Limpiando base de datos existente...")
    db.products.delete_many({})
    db.users.delete_many({})
    db.orders.delete_many({})
    db.prescriptions.delete_many({})
    
    print("🌱 Insertando productos de ejemplo...")
    result_products = db.products.insert_many(products)
    print(f"✅ {len(result_products.inserted_ids)} productos insertados")
    
    print("👤 Insertando usuarios de ejemplo...")
    result_users = db.users.insert_many(users)
    print(f"✅ {len(result_users.inserted_ids)} usuarios insertados")
    
    print("\n📊 Resumen de la base de datos:")
    print(f"   Products: {db.products.count_documents({})}")
    print(f"   Users: {db.users.count_documents({})}")
    print(f"   Orders: {db.orders.count_documents({})}")
    print(f"   Prescriptions: {db.prescriptions.count_documents({})}")
    
    print("\n🔑 Credenciales para prueba:")
    print("   Admin: admin@farmacia.com / admin123")
    print("   Cliente: cliente@ejemplo.com / cliente123")
    print("\n🎯 ¡Base de datos lista! Ejecuta 'python app.py' para iniciar el servidor.")

if __name__ == '__main__':
    seed_database()
    # Añadir al seed.py existente, en la sección de usuarios:

users = [
    {
        'email': 'admin@farmacia.com',
        'password': 'admin123',
        'role': 'admin',
        'nombre': 'María',
        'apellido': 'González',
        'telefono': '3312345678',
        'fecha_nacimiento': '1985-06-15',
        'genero': 'femenino',
        'created_at': datetime.utcnow(),
        'direccion': {
            'calle': 'Av. Chapultepec',
            'numero_exterior': '123',
            'colonia': 'Centro',
            'ciudad': 'Guadalajara',
            'estado': 'Jalisco',
            'codigo_postal': '44100',
            'referencias': 'Frente al parque'
        },
        'notifications': {
            'email_promociones': True,
            'email_pedidos': True,
            'email_recetas': True,
            'sms_notificaciones': False
        }
    },
    {
        'email': 'cliente@ejemplo.com',
        'password': 'cliente123',
        'role': 'user',
        'nombre': 'Carlos',
        'apellido': 'Rodríguez',
        'telefono': '3356789012',
        'fecha_nacimiento': '1990-03-22',
        'genero': 'masculino',
        'created_at': datetime.utcnow(),
        'direccion': {
            'calle': 'Calzada Independencia',
            'numero_exterior': '456',
            'numero_interior': 'A',
            'colonia': 'Jardines del Bosque',
            'ciudad': 'Guadalajara',
            'estado': 'Jalisco',
            'codigo_postal': '44220',
            'referencias': 'Esquina con Av. México'
        },
        'notifications': {
            'email_promociones': True,
            'email_pedidos': True,
            'email_recetas': False,
            'sms_notificaciones': True
        }
    }
]