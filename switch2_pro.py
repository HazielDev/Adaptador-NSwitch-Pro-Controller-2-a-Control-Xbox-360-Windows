"""Lectura del Nintendo Switch 2 Pro Controller conectado por USB.

El control expone tres interfaces USB:
  - MI_00: HID   -> aquí llegan los reportes de entrada (ID 0x05, 64 bytes, ~250 Hz)
  - MI_01: bulk (WinUSB) -> aquí se mandan comandos (inicialización, LEDs, ...)
  - MI_02: audio

Si nadie inicializó el control (por ejemplo, Steam cerrado), no manda
reportes por HID; en ese caso se envía la secuencia de arranque por MI_01.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import hid

VID_NINTENDO = 0x057E
PID_SWITCH2_PRO = 0x2069

REPORT_ID = 0x05
REPORT_LEN = 64

# Nombre del botón -> (byte del reporte, máscara)
BOTONES: dict[str, tuple[int, int]] = {
    "Y": (5, 0x01),
    "X": (5, 0x02),
    "B": (5, 0x04),
    "A": (5, 0x08),
    "R": (5, 0x40),
    "ZR": (5, 0x80),
    "MENOS": (6, 0x01),
    "MAS": (6, 0x02),
    "R3": (6, 0x04),
    "L3": (6, 0x08),
    "HOME": (6, 0x10),
    "CAPTURA": (6, 0x20),
    "C": (6, 0x40),
    "ABAJO": (7, 0x01),
    "ARRIBA": (7, 0x02),
    "DERECHA": (7, 0x04),
    "IZQUIERDA": (7, 0x08),
    "L": (7, 0x40),
    "ZL": (7, 0x80),
    "GR": (8, 0x01),
    "GL": (8, 0x02),
}

STICK_IZQ_OFFSET = 11
STICK_DER_OFFSET = 14

# Comandos para la interfaz bulk (MI_01)
SECUENCIA_INICIO = (
    # Activa el envío de reportes de entrada por USB
    bytes([0x03, 0x91, 0x00, 0x0D, 0x00, 0x08, 0x00, 0x00, 0x01, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]),
    # Pide el formato de reporte 0x05
    bytes([0x03, 0x91, 0x00, 0x0A, 0x00, 0x04, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00]),
    # LED de jugador 1
    bytes([0x09, 0x91, 0x00, 0x07, 0x00, 0x08, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
)


class ControlError(Exception):
    pass


@dataclass(frozen=True)
class Estado:
    botones: frozenset[str]
    lx: int  # 0..4095, ~2048 en reposo
    ly: int  # crece hacia arriba
    rx: int
    ry: int


def _leer_stick(datos: bytes, o: int) -> tuple[int, int]:
    x = datos[o] | ((datos[o + 1] & 0x0F) << 8)
    y = (datos[o + 1] >> 4) | (datos[o + 2] << 4)
    return x, y


def parsear(datos: bytes) -> Estado:
    botones = frozenset(n for n, (b, m) in BOTONES.items() if datos[b] & m)
    lx, ly = _leer_stick(datos, STICK_IZQ_OFFSET)
    rx, ry = _leer_stick(datos, STICK_DER_OFFSET)
    return Estado(botones, lx, ly, rx, ry)


def inicializar_usb() -> str | None:
    """Manda la secuencia de arranque por la interfaz bulk.

    Devuelve None si salió bien, o un texto con el error.
    """
    try:
        import libusb_package
        import usb.core
        import usb.util
    except ImportError as e:
        return f"pyusb/libusb no disponible: {e}"

    backend = libusb_package.get_libusb1_backend()
    dev = usb.core.find(idVendor=VID_NINTENDO, idProduct=PID_SWITCH2_PRO, backend=backend)
    if dev is None:
        return "el control no aparece por USB"
    try:
        intf = dev.get_active_configuration()[(1, 0)]
        es_salida = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT  # noqa: E731
        ep_out = usb.util.find_descriptor(intf, custom_match=es_salida)
        ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: not es_salida(e))
        usb.util.claim_interface(dev, 1)
        try:
            for cmd in SECUENCIA_INICIO:
                ep_out.write(cmd, timeout=500)
                try:
                    ep_in.read(64, timeout=200)
                except usb.core.USBError:
                    pass
        finally:
            usb.util.release_interface(dev, 1)
    except usb.core.USBError as e:
        return str(e)
    finally:
        usb.util.dispose_resources(dev)
    return None


class Switch2Pro:
    def __init__(self) -> None:
        self._dev: hid.device | None = None
        self._ids_vistos: set[int] = set()

    def abrir(self) -> Estado:
        """Abre el control y devuelve el primer estado leído."""
        rutas = [d["path"] for d in hid.enumerate(VID_NINTENDO, PID_SWITCH2_PRO)]
        if not rutas:
            raise ControlError("No se encontró el Switch 2 Pro Controller (¿está conectado por USB?)")
        dev = hid.device()
        dev.open_path(rutas[0])
        self._dev = dev

        estado = self._esperar_reporte(0.5)
        if estado:
            return estado

        error_usb = inicializar_usb()
        estado = self._esperar_reporte(1.5)
        if estado:
            return estado

        self.cerrar()
        if self._ids_vistos:
            ids = ", ".join(f"0x{i:02X}" for i in sorted(self._ids_vistos))
            raise ControlError(f"El control manda reportes con formato desconocido ({ids})")
        if error_usb:
            raise ControlError(
                f"No se pudo inicializar el control ({error_usb}). "
                "Desconéctalo y vuelve a conectarlo, o abre Steam."
            )
        raise ControlError("El control no responde. Desconéctalo y vuelve a conectarlo.")

    def _esperar_reporte(self, segundos: float) -> Estado | None:
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            estado = self.leer(50)
            if estado:
                return estado
        return None

    def leer(self, timeout_ms: int = 100) -> Estado | None:
        """Lee un reporte. Lanza OSError si el control se desconecta."""
        if self._dev is None:
            raise OSError("control cerrado")
        datos = self._dev.read(REPORT_LEN, timeout_ms)
        if not datos:
            return None
        if datos[0] != REPORT_ID or len(datos) < 17:
            self._ids_vistos.add(datos[0])
            return None
        return parsear(bytes(datos))

    def cerrar(self) -> None:
        if self._dev is not None:
            try:
                self._dev.close()
            finally:
                self._dev = None
