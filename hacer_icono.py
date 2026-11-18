"""Genera icono.ico (el icono del ejecutable). Solo hace falta ejecutarlo si quieres cambiar el diseño."""
from pathlib import Path

from PIL import Image, ImageDraw

LADO = 1024
FONDO = (30, 31, 36, 255)
VERDE = (34, 165, 89, 255)
CLARO = (232, 232, 236, 255)

img = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Fondo redondeado
d.rounded_rectangle((0, 0, LADO - 1, LADO - 1), radius=LADO // 5, fill=FONDO)

# Cuerpo del control
cx, cy = LADO / 2, LADO / 2 + 20
ancho, alto = LADO * 0.62, LADO * 0.34
d.rounded_rectangle((cx - ancho / 2, cy - alto / 2, cx + ancho / 2, cy + alto / 2),
                    radius=alto / 2.3, fill=VERDE)
# Agarres
for signo in (-1, 1):
    gx = cx + signo * ancho * 0.40
    d.ellipse((gx - alto * 0.52, cy - alto * 0.52, gx + alto * 0.52, cy + alto * 0.52), fill=VERDE)

# Cruceta
dx, dy = cx - ancho * 0.26, cy - alto * 0.06
b, g = alto * 0.09, alto * 0.30
d.rounded_rectangle((dx - b / 2, dy - g / 2, dx + b / 2, dy + g / 2), radius=b / 3, fill=CLARO)
d.rounded_rectangle((dx - g / 2, dy - b / 2, dx + g / 2, dy + b / 2), radius=b / 3, fill=CLARO)

# Cuatro botones
bx, by = cx + ancho * 0.26, cy - alto * 0.06
r, sep = alto * 0.075, alto * 0.17
for ox, oy in ((0, -sep), (0, sep), (-sep, 0), (sep, 0)):
    d.ellipse((bx + ox - r, by + oy - r, bx + ox + r, by + oy + r), fill=CLARO)

destino = Path(__file__).with_name("icono.ico")
img.save(destino, sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
print("escrito:", destino)
