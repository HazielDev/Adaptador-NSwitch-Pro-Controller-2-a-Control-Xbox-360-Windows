"""Traduce el estado del Switch 2 Pro Controller a un control de Xbox 360 virtual (ViGEmBus)."""
from __future__ import annotations

import math
import threading

import vgamepad as vg

from switch2_pro import ControlError, Estado, Switch2Pro

XB = vg.XUSB_BUTTON

# Botones de Nintendo -> Xbox que no dependen de la distribución A/B/X/Y
MAPA_COMUN = {
    "L": XB.XUSB_GAMEPAD_LEFT_SHOULDER,
    "R": XB.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "MENOS": XB.XUSB_GAMEPAD_BACK,
    "MAS": XB.XUSB_GAMEPAD_START,
    "HOME": XB.XUSB_GAMEPAD_GUIDE,
    "L3": XB.XUSB_GAMEPAD_LEFT_THUMB,
    "R3": XB.XUSB_GAMEPAD_RIGHT_THUMB,
    "ARRIBA": XB.XUSB_GAMEPAD_DPAD_UP,
    "ABAJO": XB.XUSB_GAMEPAD_DPAD_DOWN,
    "IZQUIERDA": XB.XUSB_GAMEPAD_DPAD_LEFT,
    "DERECHA": XB.XUSB_GAMEPAD_DPAD_RIGHT,
    # Paletas traseras: repiten el clic de los sticks
    "GL": XB.XUSB_GAMEPAD_LEFT_THUMB,
    "GR": XB.XUSB_GAMEPAD_RIGHT_THUMB,
    # "CAPTURA" y "C" no tienen equivalente en Xbox
}

# Por posición: el botón de abajo de Nintendo (B) es el de abajo de Xbox (A), etc.
MAPA_POSICION = {
    "B": XB.XUSB_GAMEPAD_A,
    "A": XB.XUSB_GAMEPAD_B,
    "Y": XB.XUSB_GAMEPAD_X,
    "X": XB.XUSB_GAMEPAD_Y,
}

# Por letra: A = A, B = B, ...
MAPA_LETRA = {
    "A": XB.XUSB_GAMEPAD_A,
    "B": XB.XUSB_GAMEPAD_B,
    "X": XB.XUSB_GAMEPAD_X,
    "Y": XB.XUSB_GAMEPAD_Y,
}

ZONA_MUERTA = 0.06
RANGO_INICIAL = 1300  # se amplía solo al mover los sticks hasta el tope


class Eje:
    """Normaliza un eje de 12 bits a -1..1 con autocalibración del rango."""

    def __init__(self, centro: int) -> None:
        self.centro = centro if abs(centro - 2048) < 400 else 2048
        self.pos = RANGO_INICIAL
        self.neg = RANGO_INICIAL

    def __call__(self, valor: int) -> float:
        d = valor - self.centro
        if d >= 0:
            self.pos = max(self.pos, d)
            return d / self.pos
        self.neg = max(self.neg, -d)
        return d / self.neg


def _zona_muerta(x: float, y: float) -> tuple[float, float]:
    m = math.hypot(x, y)
    if m < ZONA_MUERTA:
        return 0.0, 0.0
    escala = min(1.0, (m - ZONA_MUERTA) / (1 - ZONA_MUERTA)) / m
    return x * escala, y * escala


class Traductor:
    def __init__(self) -> None:
        self.por_posicion = True
        self.estado_texto = "Inactivo"
        self.error = False
        self.falta_driver = False
        self.conectado = False
        self.ultimo: Estado | None = None
        self.sticks = (0.0, 0.0, 0.0, 0.0)  # normalizados, -1..1
        self._parar = threading.Event()
        self._hilo: threading.Thread | None = None

    @property
    def activo(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    def activar(self) -> None:
        if self.activo:
            return
        self._parar.clear()
        self.error = False
        self.falta_driver = False
        self.estado_texto = "Iniciando..."
        self._hilo = threading.Thread(target=self._bucle, name="traductor", daemon=True)
        self._hilo.start()

    def desactivar(self) -> None:
        self._parar.set()
        if self._hilo is not None:
            self._hilo.join(timeout=3)
        self._hilo = None
        self.conectado = False
        self.ultimo = None
        if not self.error:
            self.estado_texto = "Inactivo"

    def _bucle(self) -> None:
        try:
            pad = vg.VX360Gamepad()
        except Exception as e:  # ViGEmBus no instalado o sin acceso
            self.error = True
            self.falta_driver = True
            self.estado_texto = (
                "Falta el driver ViGEmBus, que es el que crea el control de Xbox. "
                f"Pulsa «Instalar driver» aquí abajo.\n({e})"
            )
            return
        # Recién conectado, XInput muestra valores basura en los sticks hasta recibir
        # un reporte distinto de cero (el driver ignora reportes repetidos).
        self._parar.wait(0.3)
        pad.left_trigger(1)
        pad.update()
        pad.reset()
        pad.update()
        try:
            while not self._parar.is_set():
                self._sesion(pad)
                if not self._parar.is_set():
                    self._parar.wait(1.0)
        finally:
            pad.reset()
            pad.update()
            del pad  # desconecta el control virtual

    def _sesion(self, pad: vg.VX360Gamepad) -> None:
        control = Switch2Pro()
        try:
            primero = control.abrir()
        except (ControlError, OSError) as e:
            self.conectado = False
            self.estado_texto = f"Esperando control... {e}"
            return

        ejes = [Eje(primero.lx), Eje(primero.ly), Eje(primero.rx), Eje(primero.ry)]
        self.conectado = True
        self.error = False
        self.estado_texto = "ACTIVO: tu Pro Controller 2 ahora es un control de Xbox"
        try:
            estado: Estado | None = primero
            while not self._parar.is_set():
                if estado is not None:
                    self._enviar(pad, estado, ejes)
                estado = control.leer(100)
        except OSError:
            self.estado_texto = "Control desconectado. Reconéctalo..."
        finally:
            self.conectado = False
            self.ultimo = None
            control.cerrar()
            pad.reset()
            pad.update()

    def _enviar(self, pad: vg.VX360Gamepad, e: Estado, ejes: list[Eje]) -> None:
        self.ultimo = e
        mapa_abxy = MAPA_POSICION if self.por_posicion else MAPA_LETRA
        mascara = 0
        for nombre in e.botones:
            boton = mapa_abxy.get(nombre) or MAPA_COMUN.get(nombre)
            if boton is not None:
                mascara |= int(boton)
        pad.report.wButtons = mascara
        pad.left_trigger(255 if "ZL" in e.botones else 0)
        pad.right_trigger(255 if "ZR" in e.botones else 0)
        lx, ly = _zona_muerta(ejes[0](e.lx), ejes[1](e.ly))
        rx, ry = _zona_muerta(ejes[2](e.rx), ejes[3](e.ry))
        pad.left_joystick_float(lx, ly)
        pad.right_joystick_float(rx, ry)
        pad.update()
        self.sticks = (lx, ly, rx, ry)
