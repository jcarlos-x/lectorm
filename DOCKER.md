# Docker Setup para Lectorm

Este directorio contiene los archivos necesarios para ejecutar Lectorm usando Docker y automatizar la construcción con GitHub Actions.

## 🐳 Archivos Docker

- `Dockerfile` - Imagen optimizada multi-stage para producción
- `.dockerignore` - Excluye archivos innecesarios del build
- `.github/workflows/docker-publish.yml` - CI/CD para DockerHub

## 🚀 Uso Rápido

### Ejecutar localmente
```bash
# Construir imagen
docker build -t lectorm .

# Ejecutar contenedor
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/mangas:/app/mangas \
  -v $(pwd)/data:/app/data \
  --name lectorm \
  lectorm
```

### Usando Docker Compose (recomendado)
```yaml
version: '3.8'
services:
  lectorm:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./mangas:/app/mangas
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

## 🔧 Configuración GitHub Actions

### 1. Configurar Secrets en GitHub

Ve a tu repositorio → Settings → Secrets and variables → Actions y añade:

```
DOCKER_USERNAME: tu_usuario_dockerhub
DOCKER_TOKEN: tu_token_de_acceso_dockerhub
```

### 2. Crear Token de DockerHub

1. Ve a [DockerHub](https://hub.docker.com/)
2. Account Settings → Security → New Access Token
3. Copia el token y úsalo como `DOCKER_TOKEN`

### 3. Funcionamiento Automático

El workflow se ejecuta automáticamente cuando:
- Haces push a `main` o `master`
- Creas un Pull Request
- Creas un tag de versión (v1.0.0)

### 4. Tags de Imagen

- `latest` - Última versión de la rama principal
- `v1.0.0` - Versiones específicas (tags)
- `pr-123` - Pull requests (solo para testing)

## 📁 Estructura de Volúmenes

```
/app/mangas/    # Directorio de archivos manga (mount volume)
/app/data/      # Base de datos y configuración (mount volume)
```

## 🌟 Características

- ✅ Imagen multi-arquitectura (AMD64 + ARM64)
- ✅ Usuario no-root para seguridad
- ✅ Health check integrado
- ✅ Cache optimizado de layers
- ✅ Escaneo de vulnerabilidades con Trivy
- ✅ Build automático en CI/CD

## 🔍 Testing

### Test local
```bash
# Construir y testear
docker build -t lectorm-test .
docker run --rm -p 5000:5000 lectorm-test &
curl http://localhost:5000/login
```

### Logs del contenedor
```bash
docker logs lectorm
```

## 🛠️ Troubleshooting

### Problemas comunes

1. **Puerto ocupado**: Cambia `-p 5000:5000` por `-p 8080:5000`
2. **Permisos de volúmenes**: Asegúrate que los directorios existen
3. **Base de datos**: Se crea automáticamente al iniciar

### Variables de entorno útiles

```bash
# Modo desarrollo
-e FLASK_ENV=development

# Puerto personalizado
-e PORT=8080

# Secret key personalizada
-e SECRET_KEY=tu_clave_secreta
```

## 📋 Comandos Útiles

```bash
# Ver imágenes
docker images lectorm

# Entrar al contenedor
docker exec -it lectorm bash

# Reiniciar contenedor
docker restart lectorm

# Ver uso de recursos
docker stats lectorm

# Limpiar imágenes antiguas
docker image prune
```