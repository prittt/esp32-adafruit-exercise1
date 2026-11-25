# ============================================================
#  config.py - YOUR settings. This is the only file you edit.
#  Upload it to the ESP32 together with main.py.
#  Do NOT share this file once it contains your password/key!
# ============================================================

# --- WiFi (ESP32 supports 2.4 GHz networks only) ---
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# --- Adafruit IO (io.adafruit.com -> yellow key icon "My Key") ---
AIO_USERNAME = "YOUR_ADAFRUIT_IO_USERNAME"
AIO_KEY = "YOUR_ADAFRUIT_IO_KEY"

# --- Feed keys (must match the feeds you create on Adafruit IO) ---
TEMP_FEED = "esp32-temperature"
LED_FEED = "esp32-led"

# --- Hardware ---
LED_PIN = 2          # on-board LED of most ESP32 DevKit boards (some boards have none!)

# --- Timing ---
PUBLISH_INTERVAL = 10   # seconds between temperatures (free plan: max 30 msgs/min)
