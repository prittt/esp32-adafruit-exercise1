# Exercise 1 - ESP32 <-> Adafruit IO (MQTT) + serial port (MicroPython)
#
# Every PUBLISH_INTERVAL seconds a random temperature is generated and
#   - printed on the serial port as   TEMP:<value>
#   - published to the Adafruit IO feed TEMP_FEED (when WiFi/MQTT is up)
#
# The LED can be switched by
#   - the Adafruit IO dashboard toggle (feed LED_FEED, values ON / OFF)
#   - a line "ON" or "OFF" received on the serial port (e.g. from Node-RED);
#     the new state is also published to LED_FEED so the dashboard switch follows.
# Every LED change is reported on the serial port as   LED:ON / LED:OFF
#
# WiFi/MQTT failures are not fatal: serial keeps working and the network is retried.
#
# Edit config.py, not this file. Upload BOTH files to the board (Thonny).

import network
import time
import random
import machine
import ubinascii
import sys
import select
import ssl
from umqtt.simple import MQTTClient

# ---------------- configuration ----------------
# All personal settings live in config.py (WiFi, Adafruit IO, feeds, LED pin).
from config import (WIFI_SSID, WIFI_PASSWORD, AIO_USERNAME, AIO_KEY,
                    TEMP_FEED, LED_FEED, LED_PIN, PUBLISH_INTERVAL)

WIFI_RETRY = 20                       # seconds between WiFi reconnect attempts
MQTT_RETRY = 10                       # seconds between MQTT reconnect attempts
PING_INTERVAL = 1000                  # ms between MQTT pings (fast toggle response)
# -----------------------------------------------

AIO_SERVER = "io.adafruit.com"
AIO_PORT = 8883                       # MQTT over TLS
CLIENT_ID = b"esp32_" + ubinascii.hexlify(machine.unique_id())

TOPIC_TEMP = "{}/feeds/{}".format(AIO_USERNAME, TEMP_FEED).encode()
TOPIC_LED = "{}/feeds/{}".format(AIO_USERNAME, LED_FEED).encode()

led = machine.Pin(LED_PIN, machine.Pin.OUT)
led.value(0)

wlan = network.WLAN(network.STA_IF)
client = None

# non-blocking reader for the serial port (USB / REPL UART)
poller = select.poll()
poller.register(sys.stdin, select.POLLIN)
serial_buf = ""


def log(*args):
    print("#", *args)  # lines starting with '#' are just info for humans


def set_led(cmd, source):
    """Apply ON/OFF. Returns True if the command was valid."""
    global client
    cmd = cmd.strip().upper()
    if cmd in ("ON", "1", "TRUE"):
        led.value(1)
    elif cmd in ("OFF", "0", "FALSE"):
        led.value(0)
    else:
        log("unknown command:", cmd)
        return False
    state = "ON" if led.value() else "OFF"
    print("LED:" + state)
    # a serial command must also move the dashboard switch
    if source == "serial" and client is not None:
        try:
            client.publish(TOPIC_LED, state.encode())
        except OSError as e:
            log("publish LED failed:", e)
            client = None
    return True


def on_message(topic, msg):
    if topic == TOPIC_LED:
        set_led(msg.decode(), "mqtt")


def read_serial():
    """Collect characters from the serial port; act on complete lines."""
    global serial_buf
    while poller.poll(0):
        ch = sys.stdin.read(1)
        if not ch:
            break
        if ch in "\r\n":
            line = serial_buf.strip()
            serial_buf = ""
            if line:
                set_led(line, "serial")
        else:
            serial_buf += ch
            if len(serial_buf) > 64:
                serial_buf = ""


def wifi_start():
    wlan.active(True)
    try:
        # disable WiFi power save: otherwise incoming MQTT messages (dashboard
        # toggle) can be delayed until the board transmits something itself
        wlan.config(pm=wlan.PM_NONE)
    except Exception as e:
        log("cannot disable WiFi power save:", e)
    try:
        wlan.disconnect()
    except OSError:
        pass
    try:
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        log("connecting to WiFi", WIFI_SSID)
    except OSError as e:
        log("WiFi connect error:", e)


def mqtt_connect():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_mode = ssl.CERT_NONE   # encrypted; server cert not checked
    c = MQTTClient(CLIENT_ID, AIO_SERVER, port=AIO_PORT,
                   user=AIO_USERNAME, password=AIO_KEY, keepalive=60, ssl=ctx)
    c.set_callback(on_message)
    c.connect()
    c.subscribe(TOPIC_LED)
    c.publish(TOPIC_LED + b"/get", b"")   # get last toggle value
    log("connected to Adafruit IO as", AIO_USERNAME)
    return c


def main():
    global client
    wifi_start()
    last_wifi_try = time.time()
    next_mqtt_try = 0
    last_pub = time.time() - PUBLISH_INTERVAL
    wifi_reported = False
    last_ping = time.ticks_ms()

    while True:
        read_serial()
        now = time.time()

        # ---- network management (never blocks for long) ----
        if not wlan.isconnected():
            client = None
            wifi_reported = False
            if now - last_wifi_try >= WIFI_RETRY:
                wifi_start()
                last_wifi_try = now
        else:
            if not wifi_reported:
                log("WiFi connected:", wlan.ifconfig()[0], "power save:", wlan.config("pm"))
                wifi_reported = True
            if client is None and now >= next_mqtt_try:
                try:
                    client = mqtt_connect()
                except Exception as e:
                    log("MQTT connect failed:", e)
                    client = None
                    next_mqtt_try = now + MQTT_RETRY

        if client is not None:
            try:
                # small MQTT ping every PING_INTERVAL ms: keeps the link active so
                # the hotspot delivers incoming toggle messages right away
                if time.ticks_diff(time.ticks_ms(), last_ping) >= PING_INTERVAL:
                    client.ping()
                    last_ping = time.ticks_ms()
                client.check_msg()
            except OSError as e:
                log("MQTT error:", e)
                client = None
                next_mqtt_try = now + MQTT_RETRY

        # ---- periodic temperature ----
        if now - last_pub >= PUBLISH_INTERVAL:
            last_pub = now
            temp = round(random.uniform(18.0, 30.0), 2)
            print("TEMP:{}".format(temp))
            if client is not None:
                try:
                    client.publish(TOPIC_TEMP, str(temp).encode())
                except OSError as e:
                    log("publish TEMP failed:", e)
                    client = None
                    next_mqtt_try = now + MQTT_RETRY

        time.sleep_ms(50)


main()
