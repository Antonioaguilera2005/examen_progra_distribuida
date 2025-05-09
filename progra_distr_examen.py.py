import asyncio
import aiohttp
import json
from datetime import datetime
from bs4 import BeautifulSoup
import os

# Archivo donde se guardan los respaldos
BACKUP_FILE = "respaldo_articulos.json"

# Fuente -> nombre interno
FUENTES = {
    "https://jsonplaceholder.typicode.com/posts/1": "fuente_json",
    "https://no-existe.com/falla": "fuente_falla"  # Esto va a fallar
}

# Cargar respaldos si existen
if os.path.exists(BACKUP_FILE):
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup_por_fuente = json.load(f)
else:
    backup_por_fuente = {}

# Convierte JSON o HTML a formato común
def normalizar_articulo(raw):
    try:
        data = json.loads(raw)
        return {
            "titulo": data.get("title", "Sin título"),
            "fecha": datetime.utcnow().isoformat(),
            "contenido": data.get("body", data.get("content", ""))
        }
    except json.JSONDecodeError:
        soup = BeautifulSoup(raw, "html.parser")
        return {
            "titulo": soup.title.string if soup.title else "Sin título",
            "fecha": datetime.utcnow().isoformat(),
            "contenido": soup.get_text()
        }

# Descargar un artículo individual
async def obtener_articulo(session, url):
    try:
        async with session.get(url, timeout=5) as response:
            return await response.text()
    except Exception as e:
        print(f" Fuente falló: {url} ({e})")
        return None

# Obtener todos los artículos (usa respaldo si falla)
async def obtener_todos():
    articulos = {}
    async with aiohttp.ClientSession() as session:
        tareas = {url: obtener_articulo(session, url) for url in FUENTES}
        resultados = await asyncio.gather(*tareas.values())

        for i, url in enumerate(FUENTES):
            raw = resultados[i]
            nombre = FUENTES[url]

            if raw:
                normalizado = normalizar_articulo(raw)
                articulos[nombre] = normalizado
                backup_por_fuente[nombre] = normalizado  # actualiza respaldo
            else:
                if nombre in backup_por_fuente:
                    print(f"🔁 Usando copia de respaldo para '{nombre}'")
                    articulos[nombre] = backup_por_fuente[nombre]
                else:
                    print(f" No hay respaldo disponible para '{nombre}'")
    return articulos

# Simula envío al servidor (solo imprime)
async def enviar_al_servidor(nombre_fuente, articulo):
    print(f"\n Enviando artículo de '{nombre_fuente}' al servidor:")
    print(json.dumps(articulo, indent=2, ensure_ascii=False))

# Proceso principal
async def main():
    print(" Iniciando sistema tolerante a fallos...\n")
    articulos = await obtener_todos()

    for nombre, articulo in articulos.items():
        await enviar_al_servidor(nombre, articulo)

    # Guardar respaldos actualizados
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(backup_por_fuente, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
