# -*- coding: utf-8 -*-
"""
ESP32 - Control de iluminación por gestos (MicroPython)
--------------------------------------------------------
El ESP32 arranca en modo Access Point (red WiFi propia) y corre un
servidor HTTP simple. Una página web en el navegador detecta gestos
de la mano con MediaPipe y le avisa al ESP32 qué hacer vía peticiones
HTTP GET.

Gestos -> acción:
    Closed_Fist (puño)     -> 30% de intensidad  (enciende 1 de 3 LEDs)
    Victory (paz)          -> 70% de intensidad  (enciende 2 de 3 LEDs)
    Open_Palm (palma)      -> 100% de intensidad (enciende 3 de 3 LEDs)
    Thumb_Down (pulgar abajo) -> Modo 1: secuencia de luces (barrido)
    Thumb_Up (pulgar arriba)  -> Modo 2: secuencia de luces (parpadeo)

Los 3 LEDs son los MISMOS para representar intensidad y para las
secuencias de los modos (no hay LEDs RGB separados).

Conexión de los LEDs (con resistencia ~220-330 ohm en serie):
    LED1 -> GPIO 25
    LED2 -> GPIO 26
    LED3 -> GPIO 27

Cómo conectarte desde el navegador:
    1. Desde tu PC/celular, conéctate a la red WiFi "ESP32_Gestos"
       (contraseña: "gestos123").
    2. Abre la página control_gestos.html.
    3. En el campo de IP del ESP32, pon: 192.168.4.1
    4. Acepta el acceso a la cámara y muestra los gestos frente a ella.
"""

import network
import socket
from machine import Pin
import time

# ---------------- Configuración de la red (Access Point) ----------------
SSID = "ESP32_Gestos"
PASSWORD = "gestos123"

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD, authmode=network.AUTH_WPA2_PSK)

while not ap.active():
    time.sleep(0.1)

print("Access Point activo")
print("SSID:", SSID)
print("IP del ESP32:", ap.ifconfig()[0])  # normalmente 192.168.4.1

# ---------------- LEDs ----------------
leds = [Pin(25, Pin.OUT), Pin(26, Pin.OUT), Pin(27, Pin.OUT)]


def apagar_todos():
    for led in leds:
        led.value(0)


def set_intensidad(nivel):
    """nivel: 1 (30%), 2 (70%) o 3 (100%). Enciende esa cantidad de LEDs."""
    apagar_todos()
    for i in range(min(nivel, len(leds))):
        leds[i].value(1)


def modo1_secuencia():
    """Modo 1 (pulgar abajo): barrido de izquierda a derecha y de vuelta."""
    apagar_todos()
    for _ in range(3):
        for led in leds:
            led.value(1)
            time.sleep(0.15)
            led.value(0)
        for led in reversed(leds):
            led.value(1)
            time.sleep(0.15)
            led.value(0)
    apagar_todos()


def modo2_secuencia():
    """Modo 2 (pulgar arriba): los 3 LEDs parpadean juntos."""
    apagar_todos()
    for _ in range(5):
        for led in leds:
            led.value(1)
        time.sleep(0.2)
        apagar_todos()
        time.sleep(0.2)


# ---------------- Servidor HTTP ----------------
def parse_query(path):
    """Convierte '/gesto?tipo=puno' en ('/gesto', {'tipo': 'puno'})."""
    if "?" not in path:
        return path, {}
    ruta, qs = path.split("?", 1)
    params = {}
    for par in qs.split("&"):
        if "=" in par:
            k, v = par.split("=", 1)
            params[k] = v
    return ruta, params


def manejar_gesto(tipo):
    if tipo == "puno":
        set_intensidad(1)
    elif tipo == "paz":
        set_intensidad(2)
    elif tipo == "palma":
        set_intensidad(3)
    elif tipo == "pulgar_abajo":
        modo1_secuencia()
    elif tipo == "pulgar_arriba":
        modo2_secuencia()
    else:
        return False
    return True


addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print("Servidor HTTP escuchando en el puerto 80")

CORS_HEADERS = (
    "Access-Control-Allow-Origin: *\r\n"
    "Access-Control-Allow-Methods: GET, OPTIONS\r\n"
    "Access-Control-Allow-Headers: *\r\n"
)

while True:
    try:
        cl, addr_cliente = s.accept()
        cl.settimeout(2.0)
        solicitud = cl.recv(1024).decode("utf-8", "ignore")
        if not solicitud:
            cl.close()
            continue

        primera_linea = solicitud.split("\r\n")[0]
        partes = primera_linea.split(" ")
        metodo = partes[0] if len(partes) > 0 else "GET"
        path = partes[1] if len(partes) > 1 else "/"

        if metodo == "OPTIONS":
            # Respuesta al preflight CORS del navegador
            cl.send("HTTP/1.1 204 No Content\r\n" + CORS_HEADERS + "\r\n")
            cl.close()
            continue

        ruta, params = parse_query(path)

        if ruta == "/gesto" and "tipo" in params:
            ok = manejar_gesto(params["tipo"])
            cuerpo = "OK" if ok else "Gesto no reconocido"
        elif ruta == "/":
            cuerpo = "ESP32 Control de Gestos - usa /gesto?tipo=..."
        else:
            cuerpo = "Ruta no encontrada"

        respuesta = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n" + CORS_HEADERS +
            "Content-Length: {}\r\n\r\n{}"
        ).format(len(cuerpo), cuerpo)

        cl.send(respuesta)
        cl.close()

    except OSError as e:
        try:
            cl.close()
        except Exception:
            pass
        print("Error en la conexión:", e)
