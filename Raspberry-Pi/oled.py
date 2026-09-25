import socket
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# CALIBRATION (placeholder - replace after running calibrate_fit.py)
# ---------------------------------------------------------------------------
CAL_SLOPE = 1.0       # TODO: replace with fitted slope
CAL_INTERCEPT = 0.0   # TODO: replace with fitted intercept


def calibrate_hb(raw_index):
    """Convert the raw Hb index into an estimated Hb value in g/dL.
    Formula: Hb = slope * raw_index + intercept
    This is only meaningful once CAL_SLOPE/CAL_INTERCEPT are fitted from
    real reference data - see calibrate_fit.py.
    """
    return CAL_SLOPE * raw_index + CAL_INTERCEPT


# ---------------------------------------------------------------------------
# OLED SETUP
# ---------------------------------------------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()


def show_on_oled(lines):
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
    y = 0
    for line in lines:
        draw.text((0, y), line, font=font, fill=255)
        y += 12
    oled.image(image)
    oled.show()


# ---------------------------------------------------------------------------
# WIFI SERVER - receives data sent by the ESP32
# ---------------------------------------------------------------------------
HOST = "0.0.0.0"
PORT = 5000

show_on_oled(["Waiting for", "ESP32 data..."])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Listening for ESP32 on port {PORT}...")

    while True:
        conn, addr = server.accept()
        with conn:
            data = conn.recv(1024).decode().strip()
            if not data:
                continue

            print(f"Received from {addr}: {data}")
            try:
                red, green, ir, raw_index = data.split(",")
                raw_index = float(raw_index)
                hb_estimate = calibrate_hb(raw_index)

                show_on_oled([
                    f"Red:  {red}",
                    f"Green:{green}",
                    f"IR:   {ir}",
                    f"Hb: {hb_estimate:.2f} g/dL",
                ])

                print(f"Raw index: {raw_index:.4f} -> Hb estimate: {hb_estimate:.2f} g/dL")
            except ValueError:
                print(f"Malformed data, skipping: {data}")
