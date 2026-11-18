# Receta de PyInstaller. Para reconstruir el .exe: compilar.bat
from PyInstaller.utils.hooks import collect_all

datos, binarios, ocultos = [("icono.ico", ".")], [], []
for paquete in ("vgamepad", "libusb_package", "hid"):
    d, b, o = collect_all(paquete)
    datos += d
    binarios += b
    ocultos += o

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binarios,
    datas=datos,
    hiddenimports=ocultos + ["usb.backend.libusb1"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["PIL", "numpy", "pytest", "unittest", "pydoc_data"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Adaptador Pro Controller 2",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon="icono.ico",
)
