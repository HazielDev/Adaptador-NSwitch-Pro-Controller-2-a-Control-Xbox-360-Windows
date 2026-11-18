"""Instalación del driver ViGEmBus, necesario para crear el control de Xbox virtual.

El instalador (.msi) viene dentro del paquete vgamepad, así que también viaja
dentro del .exe: en una PC nueva se puede instalar sin descargar nada.
"""
from __future__ import annotations

import ctypes
import shutil
import sys
import tempfile
from ctypes import wintypes
from pathlib import Path

SEE_MASK_NOCLOSEPROCESS = 0x00000040
SEE_MASK_NOASYNC = 0x00000100


class _SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


def ruta_instalador() -> Path | None:
    """Ruta al .msi de ViGEmBus que acompaña a vgamepad."""
    try:
        import vgamepad
    except ImportError:
        return None
    arch = "x64" if sys.maxsize > 2**32 else "x86"
    msi = Path(vgamepad.__file__).parent / "win" / "vigem" / "install" / arch / f"ViGEmBusSetup_{arch}.msi"
    return msi if msi.is_file() else None


def driver_disponible() -> bool:
    """True si se puede crear un control virtual (es decir, ViGEmBus está instalado)."""
    try:
        import vgamepad as vg

        pad = vg.VX360Gamepad()
        del pad
        return True
    except Exception:
        return False


def instalar_driver() -> str | None:
    """Lanza el instalador del driver con permisos de administrador.

    Devuelve None si se instaló bien, o un texto con el motivo del fallo.
    """
    msi = ruta_instalador()
    if msi is None:
        return "No se encontró el instalador del driver dentro del programa."

    # El .msi vive en una carpeta temporal mientras el .exe corre; se copia a una
    # ruta estable (y sin caracteres raros) para que msiexec no tenga problemas.
    destino = Path(tempfile.gettempdir()) / msi.name
    try:
        shutil.copyfile(msi, destino)
    except OSError as e:
        return f"No se pudo preparar el instalador: {e}"

    info = _SHELLEXECUTEINFOW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NOASYNC
    info.lpVerb = "runas"  # pide permisos de administrador (aviso de Windows)
    info.lpFile = "msiexec.exe"
    info.lpParameters = f'/i "{destino}" /passive /norestart'
    info.nShow = 1

    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)):
        error = ctypes.get_last_error()
        if error == 1223:  # ERROR_CANCELLED
            return "Cancelaste el permiso de administrador."
        return "No se pudo abrir el instalador del driver."

    ctypes.windll.kernel32.WaitForSingleObject(info.hProcess, 0xFFFFFFFF)
    codigo = wintypes.DWORD()
    ctypes.windll.kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(codigo))
    ctypes.windll.kernel32.CloseHandle(info.hProcess)
    destino.unlink(missing_ok=True)

    if codigo.value == 3010:  # ERROR_SUCCESS_REBOOT_REQUIRED
        return "Instalado, pero hay que reiniciar la PC para terminar."
    if codigo.value != 0:
        return f"El instalador terminó con error {codigo.value}."
    return None
