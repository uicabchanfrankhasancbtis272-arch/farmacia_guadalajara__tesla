# init.py - Script de inicialización completo
import os
import subprocess
import sys

def setup_project():
    print("🚀 Configurando Farmacias La Guadalajara...")
    
    # Verificar Python
    try:
        subprocess.run([sys.executable, "--version"], check=True)
        print("✅ Python verificado")
    except:
        print("❌ Python no encontrado")
        return
    
    # Crear entorno virtual
    if not os.path.exists("venv"):
        print("📦 Creando entorno virtual...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("✅ Entorno virtual creado")
    
    # Instalar dependencias
    print("📚 Instalando dependencias...")
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Linux/Mac
        pip_path = "venv/bin/pip"
    
    subprocess.run([pip_path, "install", "-r", "requirements.txt"])
    print("✅ Dependencias instaladas")
    
    # Crear archivo .env si no existe
    if not os.path.exists(".env"):
        print("🔧 Creando archivo .env...")
        with open(".env", "w") as f:
            f.write("SECRET_KEY=tu_clave_secreta_muy_segura_aqui\n")
            f.write("MONGO_URI=mongodb://localhost:27017/farmacia\n")
        print("✅ Archivo .env creado")
    
    # Ejecutar seed
    print("🌱 Poblando base de datos...")
    subprocess.run([sys.executable, "seed.py"])
    
    print("\n🎉 ¡Configuración completada!")
    print("\n📝 Para iniciar la aplicación:")
    print("   Windows: venv\\Scripts\\activate && python app.py")
    print("   Linux/Mac: source venv/bin/activate && python app.py")
    print("\n🌐 La aplicación estará en: http://localhost:5000")
    print("\n🔧 Rutas especiales:")
    print("   /admin/clean - Limpiar base de datos (solo desarrollo)")
    print("   /admin/migrate-users - Migrar usuarios existentes")

if __name__ == '__main__':
    setup_project()