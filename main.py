"""Ventana principal: un botón grande para activar/desactivar la traducción."""
from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from traductor import Traductor
from vigem_setup import instalar_driver


def ruta_recurso(nombre: str) -> str:
    """Ruta a un archivo que viaja junto al programa (también dentro del .exe)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)

FONDO = "#1e1f24"
PANEL = "#2a2c33"
TEXTO = "#e8e8ec"
TEXTO_SUAVE = "#9a9cab"
VERDE = "#22a559"
VERDE_HOVER = "#1c8c4b"
ROJO = "#d64545"
ROJO_HOVER = "#b83a3a"
AMARILLO = "#e0b341"
AZUL = "#3b6fd4"
AZUL_HOVER = "#325cb0"

ORDEN_BOTONES = [
    "A", "B", "X", "Y", "L", "R", "ZL", "ZR", "MENOS", "MAS", "HOME", "CAPTURA", "C",
    "GL", "GR", "L3", "R3", "ARRIBA", "ABAJO", "IZQUIERDA", "DERECHA",
]
NOMBRES_CORTOS = {
    "MENOS": "−", "MAS": "+", "HOME": "Home", "CAPTURA": "Captura",
    "ARRIBA": "↑", "ABAJO": "↓", "IZQUIERDA": "←", "DERECHA": "→",
}


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.traductor = Traductor()

        self.title("Pro Controller 2 → Xbox")
        self.configure(bg=FONDO)
        self.geometry("480x560")
        self.minsize(420, 520)
        try:
            self.iconbitmap(ruta_recurso("icono.ico"))
        except tk.TclError:
            pass

        tk.Label(
            self, text="Switch 2 Pro Controller  →  Xbox", font=("Segoe UI", 16, "bold"),
            bg=FONDO, fg=TEXTO,
        ).pack(pady=(22, 4))
        tk.Label(
            self, text="Conectado por USB · control virtual Xbox 360 (ViGEmBus)",
            font=("Segoe UI", 9), bg=FONDO, fg=TEXTO_SUAVE,
        ).pack()

        self.boton = tk.Button(
            self, text="ACTIVAR", font=("Segoe UI", 34, "bold"), fg="white",
            bg=VERDE, activebackground=VERDE_HOVER, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", command=self.alternar,
        )
        self.boton.pack(fill="x", padx=36, pady=24, ipady=34)
        self.boton.bind("<Enter>", lambda _: self._hover(True))
        self.boton.bind("<Leave>", lambda _: self._hover(False))

        self.estado = tk.Label(
            self, text="Inactivo", font=("Segoe UI", 10), bg=FONDO, fg=TEXTO_SUAVE,
            wraplength=420, justify="center",
        )
        self.estado.pack(padx=20)

        # Solo aparece si falta el driver ViGEmBus (p. ej. en una PC nueva)
        self.zona_driver = tk.Frame(self, bg=FONDO)
        self.zona_driver.pack(fill="x")
        self.boton_driver = tk.Button(
            self.zona_driver, text="Instalar driver (ViGEmBus)", font=("Segoe UI", 11, "bold"),
            fg="white", bg=AZUL, activebackground=AZUL_HOVER, activeforeground="white",
            relief="flat", bd=0, cursor="hand2", command=self.instalar_driver,
        )

        self.por_posicion = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self, text="Botones por posición (B de Nintendo = A de Xbox)",
            variable=self.por_posicion, command=self._cambiar_mapa,
            font=("Segoe UI", 10), bg=FONDO, fg=TEXTO, selectcolor=PANEL,
            activebackground=FONDO, activeforeground=TEXTO,
        ).pack(pady=(14, 8))

        panel = tk.Frame(self, bg=PANEL)
        panel.pack(fill="both", expand=True, padx=20, pady=(4, 20))
        self.lienzo = tk.Canvas(panel, height=120, bg=PANEL, highlightthickness=0)
        self.lienzo.pack(fill="x", pady=(12, 4))
        self.botones_txt = tk.Label(
            panel, text="", font=("Segoe UI", 11, "bold"), bg=PANEL, fg=TEXTO, wraplength=400,
        )
        self.botones_txt.pack(pady=(0, 12))

        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self._refrescar()

    def _hover(self, dentro: bool) -> None:
        if self.traductor.activo:
            self.boton.configure(bg=ROJO_HOVER if dentro else ROJO)
        else:
            self.boton.configure(bg=VERDE_HOVER if dentro else VERDE)

    def _cambiar_mapa(self) -> None:
        self.traductor.por_posicion = self.por_posicion.get()

    def alternar(self) -> None:
        if self.traductor.activo:
            self.traductor.desactivar()
            self.boton.configure(text="ACTIVAR", bg=VERDE, activebackground=VERDE_HOVER)
        else:
            self.traductor.por_posicion = self.por_posicion.get()
            self.traductor.activar()
            self.boton.configure(text="DESACTIVAR", bg=ROJO, activebackground=ROJO_HOVER)

    def instalar_driver(self) -> None:
        self.boton_driver.configure(text="Instalando... acepta el aviso de Windows", state="disabled")
        resultado: list[str | None] = []

        def trabajo() -> None:
            resultado.append(instalar_driver())

        hilo = threading.Thread(target=trabajo, daemon=True)
        hilo.start()

        def esperar() -> None:
            if hilo.is_alive():
                self.after(200, esperar)
                return
            self.boton_driver.configure(text="Instalar driver (ViGEmBus)", state="normal")
            fallo = resultado[0] if resultado else "Error desconocido."
            if fallo is None:
                self.traductor.falta_driver = False
                self.traductor.error = False
                self.traductor.estado_texto = "Driver instalado. Ya puedes pulsar ACTIVAR."
                messagebox.showinfo("Listo", "Driver instalado. Ya puedes pulsar ACTIVAR.", parent=self)
            else:
                messagebox.showerror("No se pudo instalar", fallo, parent=self)

        self.after(200, esperar)

    def _refrescar(self) -> None:
        t = self.traductor
        if t.falta_driver and not self.boton_driver.winfo_ismapped():
            self.boton_driver.pack(fill="x", padx=60, pady=(10, 0), ipady=8)
        elif not t.falta_driver and self.boton_driver.winfo_ismapped():
            self.boton_driver.pack_forget()
        if not t.activo and t.error:
            # El hilo terminó por un error (p. ej. ViGEmBus): volver al estado inicial
            self.boton.configure(text="ACTIVAR", bg=VERDE, activebackground=VERDE_HOVER)
        color = ROJO if t.error else (VERDE if t.conectado else (AMARILLO if t.activo else TEXTO_SUAVE))
        self.estado.configure(text=t.estado_texto, fg=color)
        self._dibujar(t.sticks if t.conectado else (0.0, 0.0, 0.0, 0.0))
        e = t.ultimo
        if e is not None and e.botones:
            nombres = [NOMBRES_CORTOS.get(b, b) for b in ORDEN_BOTONES if b in e.botones]
            self.botones_txt.configure(text="  ".join(nombres), fg=TEXTO)
        else:
            texto = "Presiona botones para probar" if t.conectado else "—"
            self.botones_txt.configure(text=texto, fg=TEXTO_SUAVE)
        self.after(33, self._refrescar)

    def _dibujar(self, sticks: tuple[float, float, float, float]) -> None:
        c = self.lienzo
        c.delete("all")
        ancho = c.winfo_width() or 440
        r = 46
        for i, cx in enumerate((ancho * 0.3, ancho * 0.7)):
            cy = 60
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=TEXTO_SUAVE, width=2)
            x, y = sticks[2 * i], sticks[2 * i + 1]
            px, py = cx + x * r, cy - y * r
            c.create_oval(px - 8, py - 8, px + 8, py + 8, fill=VERDE if (x or y) else TEXTO_SUAVE, outline="")

    def cerrar(self) -> None:
        self.traductor.desactivar()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
