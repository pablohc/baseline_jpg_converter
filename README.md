# Baseline JPEG Converter

Convierte imágenes de EPUB a JPEG baseline (max 480x800) y corrige imágenes envueltas en SVG para compatibilidad con Crosspoint Reader y otros lectores electrónicos.

## 📁 Estructura del Repositorio

```
baseline_jpg_converter/
├── shared/              # Lógica de conversión compartida
│   ├── __init__.py
│   └── converter.py     # EpubConverterShared
├── calibre-plugin/      # Plugin de Calibre
│   ├── __init__.py
│   └── ui.py            # BaselineJPGAction
├── standalone/          # Script independiente
│   └── convert_epub.py
├── install_plugin.py    # Crea el ZIP del plugin
├── README.md
└── requirements.txt     # Dependencias para standalone
```

## 🚀 Uso

### Opción 1: Script Standalone (sin Calibre)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Convertir un EPUB individual
python standalone/convert_epub.py "ruta/al/libro.epub"

# Convertir todos los EPUBs en una carpeta
python standalone/convert_epub.py "ruta/a/epubs/"
```

**Salida:** `libro.epub` → `libro.x4.epub`

### Opción 2: Plugin de Calibre

1. **Crear el ZIP del plugin:**
   ```bash
   python install_plugin.py
   ```

2. **Instalar en Calibre:**
   - Abre Calibre
   - Ve a **Preferences → Advanced → Plugins**
   - Haz clic en **Load plugin from file**
   - Selecciona `baseline_jpg_converter.zip`
   - Reinicia Calibre

3. **Usar el plugin:**
   - Selecciona uno o más libros en la biblioteca
   - Haz clic en el botón **Baseline JPEG Converter**
   - El libro tendrá ahora dos formatos: `EPUB` (original) y `EPUBX4` (convertido)

## ✨ Características

- ✅ Convierte imágenes a JPEG baseline (no progresivo)
- ✅ Redimensiona a max 480x800px (mantiene relación de aspecto)
- ✅ Corrige **todas** las imágenes envueltas en SVG
- ✅ Asegura meta tags de portada correctos
- ✅ Convierte PNG, GIF, WebP, BMP a JPEG
- ✅ Código compartido entre plugin y script standalone

## 📦 Archivos para cada uso

| Para usar... | Usa estos archivos |
|--------------|-------------------|
| **Plugin Calibre** | `calibre-plugin/__init__.py`, `calibre-plugin/ui.py`, `shared/` |
| **Script Standalone** | `standalone/convert_epub.py`, `shared/` |
| **Instalación Plugin** | Ejecuta `install_plugin.py` |

## 🔧 Desarrollo

El módulo `shared/converter.py` contiene toda la lógica de conversión que es utilizada tanto por el plugin de Calibre como por el script standalone. Esto evita duplicación de código y facilita el mantenimiento.

### Clases principales:

- **`EpubConverterShared`** - Lógica de conversión compartida
  - `convert_image_to_baseline()` - Convierte imágenes a JPEG
  - `fix_svg_images()` - Corrige imágenes SVG
  - `ensure_cover_meta()` - Asegura meta tags de portada

## 🐛 Problema que soluciona

Algunos lectores electrónicos (como el Crosspoint Reader) no muestran correctamente:
- Imágenes JPEG progresivas
- Imágenes envueltas en elementos SVG (`<svg><image xlink:href="..."/></svg>`)

Este plugin convierte todos los formatos de imagen a JPEG baseline y reemplaza las imágenes SVG por etiquetas `<img>` estándar.

## 📝 Changelog

- **v2.0.0** - Refactorización con módulo compartido, max 480x800, salida .x4.epub
- **v1.10.0** - Archivos .x4.epub para script standalone
- **v1.9.0** - Corrige **todas** las imágenes SVG (no solo portadas)
- **v1.8.0** - Versión inicial

## 👤 Autor

Megabit - GNU GPL v3
