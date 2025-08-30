from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta
import jwt
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = './mangas'
app.config['DATABASE'] = 'manga_reader.db'

# Verificar que el directorio de mangas existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    print(f"Advertencia: El directorio de mangas {app.config['UPLOAD_FOLDER']} no existe")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializar la base de datos"""
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS mangas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manga_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                cover_image TEXT NOT NULL,
                first_page TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                description TEXT DEFAULT '',
                artist TEXT DEFAULT 'Desconocido',
                genres TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                language TEXT DEFAULT 'Español',
                status TEXT DEFAULT 'activo',
                uploaded_by TEXT DEFAULT 'Anónimo',
                views INTEGER DEFAULT 0,
                last_viewed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                manga_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (manga_id) REFERENCES mangas (id),
                UNIQUE(user_id, manga_id)
            );
        ''')

def token_required(f):
    """Decorador para verificar token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return redirect(url_for('login'))
        return f(current_user_id, *args, **kwargs)
    return decorated

def api_token_required(f):
    """Decorador para verificar token en rutas API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token') or request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'No token provided'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Unauthorized'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated

# Funciones de configuración
def get_setting(key, default_value=None):
    """Obtener un valor de configuración"""
    try:
        with get_db() as conn:
            result = conn.execute(
                'SELECT value FROM settings WHERE key = ?',
                (key,)
            ).fetchone()
            return result['value'] if result else default_value
    except:
        return default_value

def set_setting(key, value, description=None):
    """Establecer un valor de configuración"""
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, description))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False

def get_manga_directory():
    """Obtener el directorio de mangas configurado"""
    return get_setting('manga_directory', app.config['UPLOAD_FOLDER'])

def init_default_settings():
    """Inicializar configuraciones por defecto"""
    default_settings = [
        ('manga_directory', app.config['UPLOAD_FOLDER'], 'Directorio donde se almacenan los mangas'),
    ]
    
    for key, value, description in default_settings:
        if not get_setting(key):
            set_setting(key, value, description)

# Rutas de vistas principales
@app.route('/')
@token_required
def index(current_user_id):
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/manga/<int:manga_id>')
@token_required
def manga_detail(current_user_id, manga_id):
    return render_template('manga_detail.html')

@app.route('/read/<int:manga_id>')
@token_required
def reader(current_user_id, manga_id):
    return render_template('reader.html')

@app.route('/settings')
@token_required
def settings_page(current_user_id):
    return render_template('settings.html')

# API Routes - Autenticación
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No se recibieron datos'}), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'message': 'Todos los campos son requeridos'}), 400
        
        # Validaciones básicas
        if len(username) < 3:
            return jsonify({'message': 'El nombre de usuario debe tener al menos 3 caracteres'}), 400
            
        if len(password) < 6:
            return jsonify({'message': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        with get_db() as conn:
            # Verificar si el usuario ya existe
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()
            
            if existing_user:
                return jsonify({'message': 'El usuario o email ya está registrado'}), 400
            
            # Crear nuevo usuario
            password_hash = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            
        return jsonify({
            'message': 'Usuario registrado exitosamente. Por favor, inicia sesión.',
            'user': {'username': username, 'email': email}
        }), 201
        
    except Exception as e:
        print(f"Error en registro: {str(e)}")  # Para debugging
        return jsonify({'message': f'Error en el servidor: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No se recibieron datos'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Usuario y contraseña son requeridos'}), 400
        
        with get_db() as conn:
            user = conn.execute(
                'SELECT id, username, password_hash FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            
            if not user:
                return jsonify({'message': 'Usuario no encontrado'}), 401
                
            if not check_password_hash(user['password_hash'], password):
                return jsonify({'message': 'Contraseña incorrecta'}), 401
            
            # Actualizar último login
            conn.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.now(), user['id'])
            )
            
        # Generar token
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        response = jsonify({
            'message': 'Login exitoso',
            'user': {'username': user['username']}
        })
        
        response.set_cookie('token', token, max_age=24*60*60, httponly=True)
        return response
        
    except Exception as e:
        print(f"Error en login: {str(e)}")  # Para debugging
        return jsonify({'message': f'Error en el servidor: {str(e)}'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    response = jsonify({'message': 'Logout exitoso'})
    response.set_cookie('token', '', expires=0)
    return response

@app.route('/api/auth/user')
@api_token_required
def api_user_info(current_user_id):
    try:
        with get_db() as conn:
            user = conn.execute(
                'SELECT username, email FROM users WHERE id = ?',
                (current_user_id,)
            ).fetchone()
            
        if user:
            return jsonify({'user': dict(user)})
        return jsonify({'message': 'Usuario no encontrado'}), 404
        
    except Exception as e:
        return jsonify({'message': 'Error en el servidor'}), 500

# API Routes - Mangas
@app.route('/api/mangas/list')
@api_token_required
def api_manga_list(current_user_id):
    try:
        search_term = request.args.get('search', '')
        
        with get_db() as conn:
            if search_term:
                mangas = conn.execute(
                    'SELECT * FROM mangas WHERE status = "activo" AND title LIKE ? ORDER BY title',
                    (f'%{search_term}%',)
                ).fetchall()
            else:
                mangas = conn.execute(
                    'SELECT * FROM mangas WHERE status = "activo" ORDER BY title'
                ).fetchall()
        
        manga_list = []
        for manga in mangas:
            manga_dict = dict(manga)
            # Convertir strings de géneros y tags a listas
            manga_dict['genres'] = manga_dict['genres'].split(',') if manga_dict['genres'] else []
            manga_dict['tags'] = manga_dict['tags'].split(',') if manga_dict['tags'] else []
            manga_list.append(manga_dict)
        
        return jsonify(manga_list)
        
    except Exception as e:
        return jsonify({'error': 'Error al cargar los mangas'}), 500

@app.route('/api/mangas/<int:manga_id>')
@api_token_required
def api_manga_detail(current_user_id, manga_id):
    try:
        with get_db() as conn:
            manga = conn.execute(
                'SELECT * FROM mangas WHERE id = ?',
                (manga_id,)
            ).fetchone()
            
        if not manga:
            return jsonify({'error': 'Manga no encontrado'}), 404
        
        manga_dict = dict(manga)
        manga_dict['genres'] = manga_dict['genres'].split(',') if manga_dict['genres'] else []
        manga_dict['tags'] = manga_dict['tags'].split(',') if manga_dict['tags'] else []
        
        return jsonify(manga_dict)
        
    except Exception as e:
        return jsonify({'error': 'Error al cargar el manga'}), 500

@app.route('/api/mangas/<int:manga_id>/view', methods=['POST'])
@api_token_required
def api_manga_view(current_user_id, manga_id):
    try:
        with get_db() as conn:
            # Incrementar vistas
            conn.execute(
                'UPDATE mangas SET views = views + 1, last_viewed = ? WHERE id = ?',
                (datetime.now(), manga_id)
            )
            
            # Obtener manga actualizado
            manga = conn.execute(
                'SELECT * FROM mangas WHERE id = ?',
                (manga_id,)
            ).fetchone()
            
        if not manga:
            return jsonify({'error': 'Manga no encontrado'}), 404
        
        manga_dict = dict(manga)
        return jsonify(manga_dict)
        
    except Exception as e:
        return jsonify({'error': 'Error al actualizar vistas'}), 500

@app.route('/api/mangas/<int:manga_id>/images')
@api_token_required
def api_manga_images(current_user_id, manga_id):
    try:
        with get_db() as conn:
            manga = conn.execute(
                'SELECT manga_id FROM mangas WHERE id = ?',
                (manga_id,)
            ).fetchone()
            
        if not manga:
            return jsonify({'error': 'Manga no encontrado'}), 404
        
        # Buscar la carpeta real del manga
        manga_folder = None
        manga_id_clean = manga['manga_id']
        manga_base_directory = get_manga_directory()
        
        # Primero intentar con el manga_id directo
        test_folder = os.path.join(manga_base_directory, manga_id_clean)
        if os.path.exists(test_folder):
            manga_folder = test_folder
        else:
            # Buscar por nombre de carpeta original
            if os.path.exists(manga_base_directory):
                for folder_name in os.listdir(manga_base_directory):
                    folder_path = os.path.join(manga_base_directory, folder_name)
                    if os.path.isdir(folder_path):
                        # Convertir nombre de carpeta a manga_id para comparar
                        folder_manga_id = folder_name.lower().replace(' ', '-').replace('/', '-')
                        if folder_manga_id == manga_id_clean:
                            manga_folder = folder_path
                            break
        
        if not manga_folder or not os.path.exists(manga_folder):
            return jsonify({'error': 'Directorio del manga no encontrado'}), 404
        
        # Obtener lista de imágenes
        images = []
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
        try:
            for filename in os.listdir(manga_folder):
                if any(filename.lower().endswith(ext) for ext in allowed_extensions):
                    images.append({
                        'filename': filename,
                        'url': f'/manga/{manga_id_clean}/{filename}'
                    })
        except PermissionError:
            return jsonify({'error': 'Sin permisos para leer el directorio'}), 403
        
        # Ordenar imágenes naturalmente
        def natural_sort_key(item):
            import re
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', item['filename'])]
        
        images.sort(key=natural_sort_key)
        
        return jsonify({
            'images': images,
            'totalPages': len(images)
        })
        
    except Exception as e:
        print(f"Error en api_manga_images: {str(e)}")
        return jsonify({'error': f'Error al obtener imágenes: {str(e)}'}), 500

# Servir archivos de manga
@app.route('/manga/<manga_id>/<filename>')
@token_required
def serve_manga_file(current_user_id, manga_id, filename):
    # Usar la ruta configurada dinámicamente
    manga_base_directory = get_manga_directory()
    manga_folder = os.path.join(manga_base_directory, manga_id)
    if os.path.exists(manga_folder):
        return send_from_directory(manga_folder, filename)
    else:
        # Fallback: buscar por nombre de carpeta original
        if os.path.exists(manga_base_directory):
            for folder_name in os.listdir(manga_base_directory):
                folder_path = os.path.join(manga_base_directory, folder_name)
                if os.path.isdir(folder_path):
                    # Convertir nombre de carpeta a manga_id
                    folder_manga_id = folder_name.lower().replace(' ', '-').replace('/', '-')
                    if folder_manga_id == manga_id:
                        return send_from_directory(folder_path, filename)
        
        return "Archivo no encontrado", 404

@app.route('/api/refresh-library', methods=['POST'])
@api_token_required
def refresh_library(current_user_id):
    """Actualizar la biblioteca de mangas ejecutando el script de importación"""
    try:
        import subprocess
        import sys
        
        # Ejecutar el script de importación en el mismo directorio
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'import_mangas.py')
        
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            # Contar cuántos mangas hay ahora en la base de datos
            with get_db() as conn:
                count = conn.execute('SELECT COUNT(*) as total FROM mangas').fetchone()['total']
            
            return jsonify({
                'success': True, 
                'message': f'Biblioteca actualizada correctamente. Total de mangas: {count}',
                'total_mangas': count,
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Error al ejecutar el script de importación',
                'details': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error interno: {str(e)}'
        }), 500

# API Routes - Configuración
@app.route('/api/settings', methods=['GET'])
@api_token_required
def api_get_settings(current_user_id):
    """Obtener todas las configuraciones"""
    try:
        with get_db() as conn:
            settings = conn.execute(
                'SELECT key, value, description FROM settings ORDER BY key'
            ).fetchall()
            
        return jsonify({
            'success': True,
            'settings': [dict(setting) for setting in settings]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener configuraciones: {str(e)}'
        }), 500

@app.route('/api/settings', methods=['POST'])
@api_token_required
def api_update_settings(current_user_id):
    """Actualizar configuraciones"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400
            
        # Validar directorio de mangas si se está actualizando
        if 'manga_directory' in data:
            manga_dir = data['manga_directory'].strip()
            if not manga_dir:
                return jsonify({
                    'success': False, 
                    'error': 'El directorio de mangas no puede estar vacío'
                }), 400
                
            # Expandir ~ a la ruta home del usuario
            manga_dir = os.path.expanduser(manga_dir)
            
            # Verificar que el directorio existe
            if not os.path.exists(manga_dir):
                return jsonify({
                    'success': False, 
                    'error': f'El directorio {manga_dir} no existe'
                }), 400
                
            # Verificar que es un directorio
            if not os.path.isdir(manga_dir):
                return jsonify({
                    'success': False, 
                    'error': f'{manga_dir} no es un directorio válido'
                }), 400
                
            # Verificar permisos de lectura
            if not os.access(manga_dir, os.R_OK):
                return jsonify({
                    'success': False, 
                    'error': f'No tienes permisos de lectura en {manga_dir}'
                }), 400
                
            # Actualizar la configuración de la aplicación
            app.config['UPLOAD_FOLDER'] = manga_dir
        
        # Guardar todas las configuraciones
        updated_settings = []
        for key, value in data.items():
            if key == 'manga_directory':
                value = os.path.expanduser(value.strip())
                
            if set_setting(key, value):
                updated_settings.append(key)
            else:
                return jsonify({
                    'success': False, 
                    'error': f'Error al guardar la configuración {key}'
                }), 500
                
        return jsonify({
            'success': True,
            'message': f'Configuraciones actualizadas: {", ".join(updated_settings)}',
            'updated_settings': updated_settings
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al actualizar configuraciones: {str(e)}'
        }), 500

@app.route('/api/settings/validate-directory', methods=['POST'])
@api_token_required
def api_validate_directory(current_user_id):
    """Validar que un directorio existe y es accesible"""
    try:
        data = request.get_json()
        directory = data.get('directory', '').strip()
        
        if not directory:
            return jsonify({
                'success': False,
                'error': 'Directorio vacío'
            }), 400
            
        # Expandir ~ a la ruta home del usuario
        directory = os.path.expanduser(directory)
        
        # Verificaciones
        if not os.path.exists(directory):
            return jsonify({
                'success': False,
                'error': 'El directorio no existe'
            })
            
        if not os.path.isdir(directory):
            return jsonify({
                'success': False,
                'error': 'La ruta no es un directorio'
            })
            
        if not os.access(directory, os.R_OK):
            return jsonify({
                'success': False,
                'error': 'Sin permisos de lectura'
            })
            
        # Contar archivos de imagen en el directorio
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        image_count = 0
        manga_folders = 0
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    manga_folders += 1
                    # Contar imágenes en subdirectorios
                    try:
                        for file in os.listdir(item_path):
                            if os.path.splitext(file.lower())[1] in image_extensions:
                                image_count += 1
                    except:
                        pass
        except:
            pass
            
        return jsonify({
            'success': True,
            'directory': directory,
            'manga_folders': manga_folders,
            'image_count': image_count,
            'message': f'Directorio válido con {manga_folders} carpetas de manga y {image_count} imágenes'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al validar directorio: {str(e)}'
        }), 500

if __name__ == '__main__':
    init_db()
    init_default_settings()
    app.run(debug=True, host='0.0.0.0', port=5000)
