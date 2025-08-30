#!/usr/bin/env python3
"""
Script para importar mangas existentes desde la carpeta de mangas
"""

import sqlite3
import os
from datetime import datetime
import random

def get_image_files(directory):
    """Obtener lista de archivos de imagen en un directorio"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_files = []
    
    if not os.path.exists(directory):
        return image_files
    
    for filename in os.listdir(directory):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_files.append(filename)
    
    # Ordenar naturalmente
    image_files.sort()
    return image_files

def get_manga_directory():
    """Obtener el directorio de mangas desde la configuración"""
    try:
        conn = sqlite3.connect('manga_reader.db')
        cursor = conn.cursor()
        
        # Buscar la configuración del directorio de mangas
        cursor.execute("SELECT value FROM settings WHERE key = 'manga_directory'")
        result = cursor.fetchone()
        
        if result:
            manga_directory = result[0]
            # Expandir ~ a la ruta home del usuario
            manga_directory = os.path.expanduser(manga_directory)
            conn.close()
            return manga_directory
        else:
            conn.close()
            # Fallback al directorio por defecto
            return '/home/dev-pc/Documentos/Projects/lectorms/mangas'
            
    except Exception as e:
        print(f"Error al obtener directorio de mangas desde configuración: {e}")
        # Fallback al directorio por defecto
        return '/home/dev-pc/Documentos/Projects/lectorms/mangas'

def import_mangas_from_directory():
    """Importar mangas desde el directorio especificado"""
    manga_base_path = get_manga_directory()
    
    print(f"📁 Usando directorio de mangas: {manga_base_path}")
    
    if not os.path.exists(manga_base_path):
        print(f"Error: El directorio {manga_base_path} no existe")
        return
    
    # Conectar a la base de datos
    conn = sqlite3.connect('manga_reader.db')
    cursor = conn.cursor()
    
    # Limpiar mangas existentes
    cursor.execute("DELETE FROM mangas")
    print("✅ Mangas anteriores eliminados")
    
    imported_count = 0
    
    # Recorrer directorios de mangas
    for manga_folder in os.listdir(manga_base_path):
        manga_path = os.path.join(manga_base_path, manga_folder)
        
        # Verificar que sea un directorio
        if not os.path.isdir(manga_path):
            continue
        
        print(f"📚 Procesando: {manga_folder}")
        
        # Obtener imágenes del manga
        image_files = get_image_files(manga_path)
        
        if not image_files:
            print(f"  ⚠️  No se encontraron imágenes en {manga_folder}")
            continue
        
        # Generar ID único para el manga
        manga_id = manga_folder.lower().replace(' ', '-').replace('/', '-')
        
        # Información del manga
        title = manga_folder
        cover_image = f'/manga/{manga_id}/{image_files[0]}'
        first_page = f'/manga/{manga_id}/{image_files[0]}'
        page_count = len(image_files)
        
        # Generar vistas aleatorias para hacer más realista
        views = random.randint(50, 500)
        
        # Descripción básica
        description = f"Manga con {page_count} páginas. {title}"
        
        # Determinar género básico
        genre = "Manga"
        if any(word in title.lower() for word in ["hentai", "ecchi", "adult"]):
            genre = "Adulto"
        elif any(word in title.lower() for word in ["romance", "amor"]):
            genre = "Romance"
        
        # Insertar en la base de datos
        try:
            cursor.execute('''
                INSERT INTO mangas (
                    manga_id, title, cover_image, first_page, page_count,
                    description, artist, genres, tags, views, created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                manga_id,
                title,
                cover_image,
                first_page,
                page_count,
                description,
                "Autor Desconocido",
                genre,
                "Importado,Original",
                views,
                datetime.now(),
                "activo"
            ))
            
            imported_count += 1
            print(f"  ✅ Importado: {title} ({page_count} páginas)")
            
        except sqlite3.Error as e:
            print(f"  ❌ Error al importar {title}: {e}")
    
    # Confirmar cambios
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Importación completada: {imported_count} mangas importados")
    
    if imported_count > 0:
        print("\n📋 Mangas importados:")
        conn = sqlite3.connect('manga_reader.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT title, page_count, views FROM mangas ORDER BY title")
        for row in cursor.fetchall():
            print(f"  📖 {row[0]} - {row[1]} páginas - {row[2]} vistas")
        
        conn.close()

def update_manga_paths():
    """Actualizar las rutas de los mangas en la base de datos"""
    conn = sqlite3.connect('manga_reader.db')
    cursor = conn.cursor()
    
    # Obtener todos los mangas
    cursor.execute("SELECT id, manga_id FROM mangas")
    mangas = cursor.fetchall()
    
    for manga_id_db, manga_id in mangas:
        # Actualizar rutas
        cover_image = f'/manga/{manga_id}/cover.jpg'  # Se servirá dinámicamente
        first_page = f'/manga/{manga_id}/page-001.jpg'  # Se servirá dinámicamente
        
        cursor.execute('''
            UPDATE mangas 
            SET cover_image = ?, first_page = ?
            WHERE id = ?
        ''', (cover_image, first_page, manga_id_db))
    
    conn.commit()
    conn.close()
    print("✅ Rutas de mangas actualizadas")

if __name__ == '__main__':
    print("🚀 Importando mangas existentes...")
    import_mangas_from_directory()
    print("\n✨ ¡Proceso completado!")
