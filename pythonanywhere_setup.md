# PythonAnywhere Deployment Guide

## Korak 1: Kreiranje naloga
1. Idite na https://www.pythonanywhere.com
2. Kreirajte besplatan nalog
3. Odaberite Python 3.10

## Korak 2: Upload koda
1. Otvorite Bash konzolu na PythonAnywhere
2. Klonirajte ili upload-ujte kod:
```bash
git clone https://github.com/your-repo/ekg-analiza.git
# ili upload-ujte fajlove preko Files tab-a
```

## Korak 3: Instalacija zavisnosti
```bash
cd ekg-analiza
pip3.10 install --user -r requirements.txt
```

## Korak 4: Web App konfiguracija
1. Idite na Web tab
2. Kliknite "Add a new web app"
3. Odaberite "Manual configuration"
4. Odaberite Python 3.10
5. U "Code" sekciji:
   - Source code: `/home/yourusername/ekg-analiza`
   - Working directory: `/home/yourusername/ekg-analiza`
6. U "WSGI configuration file" sekciji editujte fajl:

```python
import sys
import os

# Dodajte putanju
path = '/home/yourusername/ekg-analiza'
if path not in sys.path:
    sys.path.append(path)

from app import create_app
application = create_app()
```

## Korak 5: Static files konfiguracija
U Web tab-u, dodajte static files mapping:
- URL: `/static/`
- Directory: `/home/yourusername/ekg-analiza/app/static/`

## Korak 6: Environment variables (opciono)
U Files tab-u, kreirajte `.env` fajl:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

## Korak 7: Reload web app
Kliknite "Reload" dugme u Web tab-u.

## Korak 8: Testiranje
Vaša aplikacija će biti dostupna na:
`https://yourusername.pythonanywhere.com`

## Troubleshooting

### Problem sa OpenCV
Ako OpenCV ne radi, dodajte u WSGI fajl:
```python
import cv2
# Ili instalirajte opencv-python-headless
```

### Problem sa matplotlib
```bash
pip3.10 install --user matplotlib --upgrade
```

### Logs
Proverite error logs u Web tab-u za debugging.

## Optimizacija za mobilne telefone

### Dodavanje PWA manifest
Kreirajte `app/static/manifest.json`:
```json
{
  "name": "EKG Analiza",
  "short_name": "EKG",
  "description": "Analiza EKG signala iz fotografija",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#667eea",
  "icons": [
    {
      "src": "/static/images/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/images/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Dodavanje u HTML head:
```html
<link rel="manifest" href="/static/manifest.json">
```

## Performance optimizacija

### Kompresija slika
```python
# U image_processing.py dodati kompresiju
from PIL import Image
import io

def compress_image(image_data, quality=85):
    img = Image.open(io.BytesIO(image_data))
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    return output.getvalue()
```

### Caching
```python
# U routes.py dodati cache headers
from flask import make_response

@api.get("/static/<path:filename>")
def static_files(filename):
    response = make_response(send_from_directory('static', filename))
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response
```