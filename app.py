import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import urllib.parse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-123')

# Configuración de MongoDB para Render
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    # Si no hay MONGO_URI, usa una base de datos local (SQLite alternativa)
    print("⚠️  MONGO_URI no encontrada. Usando modo sin base de datos.")
    # Aquí podrías agregar una alternativa como SQLite

try:
    if MONGO_URI:
        client = MongoClient(MONGO_URI)
        db = client.get_database()
        client.admin.command('ping')
        print("✅ Conectado a MongoDB correctamente")
    else:
        db = None
        print("⚠️  Modo sin base de datos activado")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    db = None
    
# Util: validar extensiones
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# Función helper para asegurar que el usuario tenga notificaciones
def ensure_user_notifications(user):
    if user is None:
        return None
    if 'notifications' not in user:
        user['notifications'] = {
            'email_promociones': True,
            'email_pedidos': True,
            'email_recetas': True,
            'sms_notificaciones': False
        }
    return user

# Función helper para asegurar que el usuario tenga dirección
def ensure_user_address(user):
    if user is None:
        return None
    if 'direccion' not in user:
        user['direccion'] = {
            'calle': '',
            'numero_exterior': '',
            'numero_interior': '',
            'colonia': '',
            'ciudad': 'Guadalajara',
            'estado': 'Jalisco',
            'codigo_postal': '',
            'referencias': ''
        }
    return user

# Función helper para obtener usuario seguro con todas las estructuras
def get_safe_user(user_id):
    if not user_id:
        return None
    
    try:
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            user = ensure_user_notifications(user)
            user = ensure_user_address(user)
        return user
    except:
        return None

# Context processor para año actual
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# RUTA: Home - catálogo con búsqueda
@app.route('/')
def index():
    query = request.args.get('q', '')
    if query:
        productos = list(db.products.find({
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}}
            ]
        }))
    else:
        productos = list(db.products.find())
    return render_template('index.html', productos=productos, query=query)

# RUTA: Ver producto
@app.route('/product/<pid>')
def product_detail(pid):
    try:
        producto = db.products.find_one({'_id': ObjectId(pid)})
        if not producto:
            flash('Producto no encontrado')
            return redirect(url_for('index'))
        return render_template('product_detail.html', producto=producto)
    except Exception as e:
        flash('ID de producto inválido')
        return redirect(url_for('index'))

# RUTA: Añadir al carrito (session simple)
@app.route('/cart/add/<pid>', methods=['POST'])
def add_to_cart(pid):
    try:
        cantidad = int(request.form.get('cantidad', 1))
        if cantidad < 1:
            flash('Cantidad debe ser mayor a 0')
            return redirect(url_for('product_detail', pid=pid))
        
        # Verificar que el producto existe
        producto = db.products.find_one({'_id': ObjectId(pid)})
        if not producto:
            flash('Producto no encontrado')
            return redirect(url_for('index'))
        
        cart = session.get('cart', {})
        str_pid = str(pid)
        cart[str_pid] = cart.get(str_pid, 0) + cantidad
        session['cart'] = cart
        flash(f'✅ {producto["name"]} añadido al carrito')
        return redirect(url_for('product_detail', pid=pid))
    except Exception as e:
        flash('Error al añadir al carrito')
        return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0.0
    
    for pid, qty in cart.items():
        try:
            prod = db.products.find_one({'_id': ObjectId(pid)})
            if prod:
                subtotal = float(prod['price']) * qty
                total += subtotal
                items.append({
                    'producto': prod, 
                    'cantidad': qty, 
                    'subtotal': subtotal,
                    'id': pid
                })
        except:
            continue
    
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/update/<pid>', methods=['POST'])
def update_cart(pid):
    try:
        cantidad = int(request.form.get('cantidad', 1))
        cart = session.get('cart', {})
        str_pid = str(pid)
        
        if cantidad <= 0:
            if str_pid in cart:
                del cart[str_pid]
        else:
            cart[str_pid] = cantidad
            
        session['cart'] = cart
        flash('Carrito actualizado')
    except:
        flash('Error al actualizar carrito')
    
    return redirect(url_for('cart'))

@app.route('/cart/remove/<pid>')
def remove_from_cart(pid):
    cart = session.get('cart', {})
    str_pid = str(pid)
    if str_pid in cart:
        del cart[str_pid]
        session['cart'] = cart
        flash('Producto eliminado del carrito')
    return redirect(url_for('cart'))

# RUTA: Checkout (simulado)
@app.route('/checkout', methods=['GET','POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Carrito vacío')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        user_email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        
        if not user_email:
            flash('Por favor ingresa tu correo electrónico')
            return redirect(url_for('checkout'))
        
        # Crear orden
        order = {
            'user_email': user_email,
            'address': address,
            'items': [],
            'total': 0.0,
            'status': 'pendiente',
            'created_at': datetime.utcnow()
        }
        
        total = 0.0
        for pid, qty in cart.items():
            try:
                prod = db.products.find_one({'_id': ObjectId(pid)})
                if prod:
                    subtotal = float(prod['price']) * qty
                    total += subtotal
                    order['items'].append({
                        'product_id': prod['_id'],
                        'name': prod['name'],
                        'qty': qty, 
                        'price': prod['price'],
                        'subtotal': subtotal
                    })
            except:
                continue
        
        order['total'] = total
        
        try:
            db.orders.insert_one(order)
            session['cart'] = {}
            flash('✅ ¡Orden creada con éxito! Te contactaremos pronto.')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Error al crear la orden')
    
    return render_template('checkout.html')

# RUTA: Registro
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        telefono = request.form.get('telefono', '').strip()
        
        if not email or not password:
            flash('Por favor completa todos los campos requeridos')
            return redirect(url_for('register'))
        
        existing = db.users.find_one({'email': email})
        if existing:
            flash('Usuario ya existe')
            return redirect(url_for('login'))
        
        user = {
            'email': email, 
            'password': password,  # En producción usar hashing!
            'nombre': nombre,
            'apellido': apellido,
            'telefono': telefono,
            'created_at': datetime.utcnow(),
            'role': 'user',
            'notifications': {
                'email_promociones': True,
                'email_pedidos': True,
                'email_recetas': True,
                'sms_notificaciones': False
            },
            'direccion': {
                'calle': '',
                'numero_exterior': '',
                'numero_interior': '',
                'colonia': '',
                'ciudad': 'Guadalajara',
                'estado': 'Jalisco',
                'codigo_postal': '',
                'referencias': ''
            }
        }
        
        try:
            db.users.insert_one(user)
            flash('✅ Registro exitoso, por favor inicia sesión')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Error en el registro')
    
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = db.users.find_one({'email': email, 'password': password})
        if user:
            session['user'] = str(user['_id'])
            session['user_email'] = user['email']
            flash(f'✅ Bienvenido {user.get("nombre", user["email"])}')
            return redirect(url_for('index'))
        flash('❌ Credenciales incorrectas')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_email', None)
    flash('Sesión cerrada')
    return redirect(url_for('index'))

# RUTA: Perfil principal
@app.route('/profile')
def profile():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    # Obtener órdenes y recetas de forma segura
    try:
        orders = list(db.orders.find({'user_email': user['email']}).sort('created_at', -1).limit(5))
        prescriptions = list(db.prescriptions.find({'email': user['email']}).sort('uploaded_at', -1))
    except Exception as e:
        orders = []
        prescriptions = []
        print(f"Error obteniendo datos del perfil: {e}")
    
    return render_template('profile.html', user=user, orders=orders, prescriptions=prescriptions)

# RUTA: Historial completo de compras
@app.route('/profile/order-history')
def order_history():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    # Obtener todos los pedidos del usuario
    try:
        orders = list(db.orders.find({'user_email': user['email']}).sort('created_at', -1))
    except Exception as e:
        orders = []
        print(f"Error obteniendo historial de pedidos: {e}")
    
    # Estadísticas
    total_orders = len(orders)
    total_spent = sum(order.get('total', 0) for order in orders)
    pending_orders = len([order for order in orders if order.get('status') == 'pendiente'])
    completed_orders = len([order for order in orders if order.get('status') == 'completado'])
    
    return render_template('order_history.html', 
                         user=user,
                         orders=orders,
                         total_orders=total_orders,
                         total_spent=total_spent,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders)

# RUTA: Detalle de pedido individual
@app.route('/profile/order/<order_id>')
def order_detail(order_id):
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    try:
        order = db.orders.find_one({'_id': ObjectId(order_id), 'user_email': user['email']})
        if not order:
            flash('Pedido no encontrado')
            return redirect(url_for('order_history'))
    except:
        flash('ID de pedido inválido')
        return redirect(url_for('order_history'))
    
    return render_template('order_detail.html', user=user, order=order)

# RUTA: Reordenar pedido
@app.route('/profile/order/<order_id>/reorder', methods=['POST'])
def reorder(order_id):
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    try:
        # Obtener el pedido original
        original_order = db.orders.find_one({'_id': ObjectId(order_id), 'user_email': user['email']})
        if not original_order:
            flash('Pedido no encontrado')
            return redirect(url_for('order_history'))
        
        # Crear nuevo carrito con los productos del pedido original
        cart = {}
        for item in original_order.get('items', []):
            if 'product_id' in item:
                product_id = str(item['product_id'])
                cart[product_id] = item.get('qty', 1)
        
        session['cart'] = cart
        flash('✅ Productos añadidos al carrito. Revisa y completa tu pedido.')
        return redirect(url_for('cart'))
        
    except Exception as e:
        flash('❌ Error al reordenar')
        return redirect(url_for('order_history'))

# RUTA: Editar perfil
@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Actualizar información del usuario
        update_data = {
            'nombre': request.form.get('nombre', '').strip(),
            'apellido': request.form.get('apellido', '').strip(),
            'telefono': request.form.get('telefono', '').strip(),
            'fecha_nacimiento': request.form.get('fecha_nacimiento', ''),
            'genero': request.form.get('genero', ''),
            'updated_at': datetime.utcnow()
        }
        
        # Actualizar dirección
        update_data['direccion'] = {
            'calle': request.form.get('calle', '').strip(),
            'numero_exterior': request.form.get('numero_exterior', '').strip(),
            'numero_interior': request.form.get('numero_interior', '').strip(),
            'colonia': request.form.get('colonia', '').strip(),
            'ciudad': request.form.get('ciudad', 'Guadalajara'),
            'estado': request.form.get('estado', 'Jalisco'),
            'codigo_postal': request.form.get('codigo_postal', '').strip(),
            'referencias': request.form.get('referencias', '').strip()
        }
        
        try:
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            flash('✅ Perfil actualizado correctamente')
            return redirect(url_for('profile'))
        except Exception as e:
            flash('❌ Error al actualizar el perfil')
    
    return render_template('edit_profile.html', user=user)

# RUTA: Cambiar contraseña
@app.route('/profile/change-password', methods=['GET', 'POST'])
def change_password():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verificar contraseña actual (en producción usar hashing)
        if user.get('password') != current_password:
            flash('❌ La contraseña actual es incorrecta')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('❌ Las nuevas contraseñas no coinciden')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 6:
            flash('❌ La contraseña debe tener al menos 6 caracteres')
            return redirect(url_for('change_password'))
        
        try:
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'password': new_password,
                    'updated_at': datetime.utcnow()
                }}
            )
            flash('✅ Contraseña actualizada correctamente')
            return redirect(url_for('profile'))
        except Exception as e:
            flash('❌ Error al cambiar la contraseña')
    
    return render_template('change_password.html')

# RUTA: Mis recetas
@app.route('/profile/prescriptions')
def my_prescriptions():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    try:
        prescriptions = list(db.prescriptions.find({'email': user['email']}).sort('uploaded_at', -1))
    except:
        prescriptions = []
    
    return render_template('my_prescriptions.html', prescriptions=prescriptions, user=user)

# RUTA: Direcciones guardadas
@app.route('/profile/addresses')
def my_addresses():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    return render_template('my_addresses.html', user=user)

# RUTA: Configuración de notificaciones
@app.route('/profile/notifications', methods=['GET', 'POST'])
def notification_settings():
    user_id = session.get('user')
    if not user_id:
        return redirect(url_for('login'))
    
    user = get_safe_user(user_id)
    if not user:
        flash('Usuario no encontrado')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        notification_settings = {
            'email_promociones': 'email_promociones' in request.form,
            'email_pedidos': 'email_pedidos' in request.form,
            'email_recetas': 'email_recetas' in request.form,
            'sms_notificaciones': 'sms_notificaciones' in request.form,
            'updated_at': datetime.utcnow()
        }
        
        try:
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'notifications': notification_settings}}
            )
            flash('✅ Configuración de notificaciones actualizada')
            return redirect(url_for('profile'))
        except Exception as e:
            flash('❌ Error al actualizar la configuración')
    
    return render_template('notification_settings.html', user=user)

# RUTA: Subir receta (prescription)
@app.route('/prescription/upload', methods=['GET','POST'])
def upload_prescription():
    if request.method == 'POST':
        file = request.files.get('prescription')
        user_email = request.form.get('email', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not user_email:
            flash('Por favor ingresa tu correo electrónico')
            return redirect(request.url)
        
        if not file or file.filename == '':
            flash('Por favor selecciona un archivo')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Tipo de archivo no permitido. Use PNG, JPG, JPEG o GIF')
            return redirect(request.url)
        
        try:
            filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            
            doc = {
                'email': user_email, 
                'filename': filename,
                'original_filename': file.filename,
                'notes': notes,
                'uploaded_at': datetime.utcnow(), 
                'status': 'pending'
            }
            
            db.prescriptions.insert_one(doc)
            flash('✅ Receta subida correctamente. Será revisada por nuestro equipo.')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Error al subir la receta')
    
    return render_template('upload_prescription.html')

# RUTA: Admin - gestionar productos
@app.route('/admin/products', methods=['GET','POST'])
def admin_products():
    if not session.get('user'):
        flash('Por favor inicia sesión')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '0')
        desc = request.form.get('description', '').strip()
        category = request.form.get('category', 'general').strip()
        
        if not name or not price:
            flash('Nombre y precio son obligatorios')
            return redirect(url_for('admin_products'))
        
        try:
            price = float(price)
            if price <= 0:
                flash('El precio debe ser mayor a 0')
                return redirect(url_for('admin_products'))
        except:
            flash('Precio inválido')
            return redirect(url_for('admin_products'))
        
        file = request.files.get('image')
        filename = None
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                flash('Tipo de imagen no permitido')
                return redirect(url_for('admin_products'))
        
        prod = {
            'name': name, 
            'price': price, 
            'description': desc,
            'category': category,
            'image': filename,
            'created_at': datetime.utcnow(),
            'active': True
        }
        
        try:
            db.products.insert_one(prod)
            flash('✅ Producto creado exitosamente')
            return redirect(url_for('admin_products'))
        except Exception as e:
            flash('Error al crear producto')
    
    try:
        productos = list(db.products.find().sort('created_at', -1))
    except:
        productos = []
    
    return render_template('admin_products.html', productos=productos)

# RUTA: Eliminar producto (solo admin)
@app.route('/admin/products/delete/<pid>', methods=['POST'])
def delete_product(pid):
    if not session.get('user'):
        flash('Por favor inicia sesión')
        return redirect(url_for('login'))
    
    try:
        # Verificar que el producto existe
        producto = db.products.find_one({'_id': ObjectId(pid)})
        if not producto:
            flash('Producto no encontrado')
            return redirect(url_for('admin_products'))
        
        # Eliminar el producto
        result = db.products.delete_one({'_id': ObjectId(pid)})
        
        if result.deleted_count > 0:
            # También eliminar la imagen si existe
            if producto.get('image'):
                try:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], producto['image'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error eliminando imagen: {e}")
            
            flash('✅ Producto eliminado correctamente')
        else:
            flash('❌ Error al eliminar el producto')
            
    except Exception as e:
        flash('❌ Error al eliminar el producto')
    
    return redirect(url_for('admin_products'))

# RUTA: Editar producto (solo admin)
@app.route('/admin/products/edit/<pid>', methods=['GET', 'POST'])
def edit_product(pid):
    if not session.get('user'):
        flash('Por favor inicia sesión')
        return redirect(url_for('login'))
    
    try:
        producto = db.products.find_one({'_id': ObjectId(pid)})
        if not producto:
            flash('Producto no encontrado')
            return redirect(url_for('admin_products'))
        
        if request.method == 'POST':
            # Actualizar información del producto
            update_data = {
                'name': request.form.get('name', '').strip(),
                'price': float(request.form.get('price', 0)),
                'description': request.form.get('description', '').strip(),
                'category': request.form.get('category', 'general').strip(),
                'active': 'active' in request.form,
                'updated_at': datetime.utcnow()
            }
            
            # Manejar nueva imagen si se subió
            file = request.files.get('image')
            if file and file.filename != '':
                if allowed_file(file.filename):
                    # Eliminar imagen anterior si existe
                    if producto.get('image'):
                        try:
                            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], producto['image'])
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        except Exception as e:
                            print(f"Error eliminando imagen anterior: {e}")
                    
                    # Guardar nueva imagen
                    filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_data['image'] = filename
                else:
                    flash('Tipo de imagen no permitido')
                    return redirect(url_for('edit_product', pid=pid))
            
            try:
                db.products.update_one(
                    {'_id': ObjectId(pid)},
                    {'$set': update_data}
                )
                flash('✅ Producto actualizado correctamente')
                return redirect(url_for('admin_products'))
            except Exception as e:
                flash('❌ Error al actualizar el producto')
        
        return render_template('edit_product.html', producto=producto)
        
    except Exception as e:
        flash('❌ Error al cargar el producto')
        return redirect(url_for('admin_products'))

# Ruta para servir imágenes estáticas
@app.route('/images/<filename>')
def images(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Ruta para limpiar la base de datos (solo desarrollo)
@app.route('/admin/clean')
def admin_clean():
    if app.debug:  # Solo en modo desarrollo
        db.products.delete_many({})
        db.users.delete_many({})
        db.orders.delete_many({})
        db.prescriptions.delete_many({})
        flash('Base de datos limpiada (solo desarrollo)')
    return redirect(url_for('index'))

# Ruta para migrar usuarios existentes (solo desarrollo)
@app.route('/admin/migrate-users')
def migrate_users():
    if app.debug:  # Solo en modo desarrollo
        users = db.users.find({})
        updated_count = 0
        
        for user in users:
            update_data = {}
            
            # Agregar notificaciones si no existen
            if 'notifications' not in user:
                update_data['notifications'] = {
                    'email_promociones': True,
                    'email_pedidos': True,
                    'email_recetas': True,
                    'sms_notificaciones': False
                }
            
            # Agregar dirección si no existe
            if 'direccion' not in user:
                update_data['direccion'] = {
                    'calle': '',
                    'numero_exterior': '',
                    'numero_interior': '',
                    'colonia': '',
                    'ciudad': 'Guadalajara',
                    'estado': 'Jalisco',
                    'codigo_postal': '',
                    'referencias': ''
                }
            
            if update_data:
                db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': update_data}
                )
                updated_count += 1
        
        flash(f'✅ {updated_count} usuarios migrados correctamente')
    return redirect(url_for('index'))

# Manejo de errores 404
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Manejo de errores 500
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)