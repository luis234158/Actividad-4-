# Control de Iluminación por Gestos — ESP32 + MediaPipe

Proyecto UMNG: sistema de control de iluminación basado en gestos de la mano, usando el **Gesture Recognizer** de MediaPipe (en el navegador) y un **ESP32** en modo Access Point (MicroPython).

Referencia de la librería usada: [MediaPipe Gesture Recognizer (Web)](https://google-ai-edge.github.io/mediapipe-samples-web/#/vision/gesture_recognizer)

## Archivos

- **`esp32_control_gestos.py`** — Firmware MicroPython del ESP32. Crea una red WiFi propia (Access Point) y un servidor HTTP que recibe el gesto detectado y controla 3 LEDs.
- **`control_gestos.html`** — Página web que usa la cámara del computador y el modelo de gestos de MediaPipe para detectar la seña y avisarle al ESP32 por HTTP.

## Cómo funciona

1. El ESP32 arranca como Access Point con SSID `ESP32_Gestos` (contraseña `gestos123`), con IP fija `192.168.4.1`.
2. Te conectas a esa red WiFi desde tu computador y abres `control_gestos.html` en el navegador.
3. La página pide acceso a la cámara, carga el modelo de MediaPipe y en cada cuadro de video detecta si hay un gesto reconocido.
4. Según el gesto detectado, la página hace una petición `fetch` al ESP32 (`http://192.168.4.1/gesto?tipo=...`).
5. El ESP32 recibe la petición y actúa sobre 3 LEDs (los mismos para intensidad y para las secuencias de los modos):

| Gesto (MediaPipe) | Acción | Parámetro enviado |
|---|---|---|
| Closed_Fist (puño) | 30% intensidad → enciende 1 LED | `puno` |
| Victory (paz) | 70% intensidad → enciende 2 LEDs | `paz` |
| Open_Palm (palma abierta) | 100% intensidad → enciende 3 LEDs | `palma` |
| Thumb_Down (pulgar abajo) | Modo 1: secuencia de barrido | `pulgar_abajo` |
| Thumb_Up (pulgar arriba) | Modo 2: secuencia de parpadeo | `pulgar_arriba` |

## Conexión de hardware

```
LED1 -> GPIO 25 (+ resistencia ~220-330 ohm)
LED2 -> GPIO 26 (+ resistencia ~220-330 ohm)
LED3 -> GPIO 27 (+ resistencia ~220-330 ohm)
GND de cada LED -> GND del ESP32
```

## Cómo correrlo

1. Sube `esp32_control_gestos.py` al ESP32 (por ejemplo como `main.py` desde Thonny o VS Code con MicroPico) para que arranque solo al encenderlo.
2. Conéctate desde tu PC a la red WiFi `ESP32_Gestos`.
3. Abre `control_gestos.html` directamente en el navegador (doble clic al archivo).
4. Autoriza el acceso a la cámara y muestra los gestos frente a ella.

## Nota sobre CORS

El servidor del ESP32 responde con encabezados `Access-Control-Allow-Origin: *` para que el navegador permita la petición desde el archivo HTML local hacia la IP del ESP32.

## Autor

Luis Miguel Ruiz — Ingeniería Mecatrónica, Universidad Militar Nueva Granada.
