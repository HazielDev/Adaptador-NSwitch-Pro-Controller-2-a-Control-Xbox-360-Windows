# Adaptador Switch 2 Pro Controller → Xbox

  Ventana con un botón **ACTIVAR** que convierte el Nintendo Switch 2 Pro Controller
  (conectado por USB) en un control de Xbox 360 virtual, para que cualquier juego de PC lo reconozca.

## Uso diario

1. Conecta el control por USB.
2. Doble clic en el acceso directo **Adaptador Pro Controller 2** del escritorio.
3. Pulsa **ACTIVAR**. Los círculos muestran los sticks y abajo aparecen los botones presionados.

No hace falta Python ni VS Code: el ejecutable (`dist\Adaptador Pro Controller 2.exe`) lleva todo dentro.
Puedes moverlo o copiarlo a otra carpeta; es un solo archivo.

## Pasarlo a otra PC

Copia solo `dist\Adaptador Pro Controller 2.exe`. No hace falta Python ni el resto del proyecto.
En la otra PC:

1. Windows avisará que el programa no está firmado: "Más información" → "Ejecutar de todas formas".
2. Al pulsar **ACTIVAR**, si falta el driver ViGEmBus aparece un botón **Instalar driver**.
   Pulsarlo instala el driver (pide permisos de administrador); viene dentro del `.exe`, no descarga nada.
3. Volver a pulsar **ACTIVAR**.

Requiere Windows 10 u 11 de 64 bits.

## Mapeo

| Switch 2 Pro | Xbox |
|---|---|
| B / A / Y / X | A / B / X / Y (por posición; la casilla cambia a "por letra") |
| L / R | LB / RB |
| ZL / ZR | LT / RT (digitales, 0 o 100 %) |
| − / + | Back / Start |
| Home | Guide |
| Clic de sticks | LS / RS |
| GL / GR (paletas traseras) | LS / RS |
| Cruceta | Cruceta |
| Captura, C | sin asignar |

Para cambiarlo, edita `MAPA_COMUN`, `MAPA_POSICION` y `MAPA_LETRA` en [traductor.py](traductor.py)
y vuelve a compilar con `compilar.bat`.

## Notas

- **Al pulsar ACTIVAR no toques los sticks:** en ese momento se toma su posición de reposo.
- **Steam abierto:** Steam también inicializa el control y puede bloquear la interfaz USB de comandos.
  No es problema: el adaptador sigue leyendo los datos por HID.
- **Doble entrada:** si un juego ya soporta el Pro Controller 2 directamente (o por Steam Input),
  verá dos controles. Desactiva Steam Input para ese juego, o usa
  [HidHide](https://github.com/nefarius/HidHide) para ocultar el control original.
- **Vibración:** no está implementada (el HD Rumble de Switch 2 usa un protocolo distinto).
- **Windows Defender:** la primera vez puede avisar porque el `.exe` no está firmado digitalmente.
  Elige "Más información" → "Ejecutar de todas formas".

## Desarrollo

Requisitos: Windows 10/11, Python 3.10+ y el driver
[ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) (ya instalado en esta PC).

| Acción | Comando |
|---|---|
| Ejecutar desde el código | `iniciar.bat` |
| Reconstruir el `.exe` | `compilar.bat` (cierra el adaptador antes) |
| Cambiar el icono | editar y ejecutar `hacer_icono.py` (necesita Pillow) |

### Archivos

- [main.py](main.py): ventana (Tkinter)
- [traductor.py](traductor.py): mapeo y control virtual Xbox (vgamepad/ViGEmBus)
- [switch2_pro.py](switch2_pro.py): lectura del control por HID e inicialización USB
- [adaptador.spec](adaptador.spec): receta de PyInstaller para el ejecutable
