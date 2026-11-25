# Exercise 1 – ESP32 ↔ Adafruit IO (MQTT) ↔ Node-RED

An ESP32 running **MicroPython**:

- generates a **random temperature** every 10 s, sends it to **Adafruit IO** over MQTT (shown on a dashboard chart) **and** prints it on the **serial port**;
- has an **LED** that can be switched **ON / OFF** from:
  - a **toggle on the Adafruit IO dashboard**,
  - a line `ON` / `OFF` written on the **serial port** (e.g. from **Node-RED**). The new state is also published to Adafruit IO, so the dashboard switch follows.

**Node-RED** reads the serial port, shows the data in the debug panel, sends ON/OFF commands over serial, and can also publish to and read from Adafruit IO directly.

```
                 MQTT over TLS (8883)
   ┌──────────────────────────────────────────┐
   │                                          ▼
┌──┴────┐  USB serial  ┌──────────┐  MQTT  ┌─────────────┐
│ ESP32 │◄────────────►│ Node-RED │◄──────►│ Adafruit IO │──► Dashboard
└───────┘  TEMP:/LED:  └──────────┘        └─────────────┘    (chart + toggle)
           ON / OFF
```

## Repository contents

| Path | What it is |
|---|---|
| `esp32/config.py` | **Your settings**: WiFi, Adafruit IO username/key, feed names, LED pin. The only file you edit. |
| `esp32/main.py` | The program for the ESP32 (MicroPython). No need to edit it. |
| `node-red/flow.json` | Node-RED flow to import (serial + Adafruit IO). |

## What you need

- An ESP32 board (e.g. ESP32 DevKit) and a **USB data cable**
- [Thonny](https://thonny.org) (to flash MicroPython and upload the code)
- [Node-RED](https://nodered.org/docs/getting-started/local) (`npm install -g --unsafe-perm node-red`)
- A free [Adafruit IO](https://io.adafruit.com) account
- A **2.4 GHz** WiFi network (a phone hotspot works; the ESP32 cannot see 5 GHz networks)
- If Windows does not show a COM port for the board: the USB-serial driver ([CP210x](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) or [CH340](https://www.wch-ic.com/downloads/CH341SER_EXE.html), depending on the chip near the USB connector)

---

## Step 1 – Adafruit IO: feeds and dashboard

1. Log in to [io.adafruit.com](https://io.adafruit.com).
2. **Feeds → New Feed**: create `esp32-temperature`.
3. **Feeds → New Feed**: create `esp32-led`.
4. **Dashboards → New Dashboard**: e.g. `ESP32 Exercise 1`, then open it.
5. **New Block → Line Chart**: select feed `esp32-temperature` → *Next step* → title `Temperature` → *Create block*.
6. **New Block → Toggle**: select feed `esp32-led` → *Next step* → leave **ON** / **OFF** as button texts → *Create block*.
7. Click the **yellow key icon** (top right) and note your **Username** and **Active Key**. You need them in steps 3 and 5.

> Free plan limit: **30 messages per minute**. The code sends one temperature every 10 s, which is well below the limit.

## Step 2 – Flash MicroPython on the ESP32 (only once per board)

Skip this step if your board already runs MicroPython (Thonny shows a `>>>` prompt).

1. Plug in the ESP32 and open **Thonny**.
2. **Tools → Options → Interpreter** → select **MicroPython (ESP32)** and your port (e.g. `COM3`, `/dev/ttyUSB0`).
3. Click **Install or update MicroPython (esptool)** (bottom right):
   - family **ESP32**, variant **Espressif • ESP32 / WROOM**, latest version → **Install**.
4. If it says *"Wrong boot mode"* or *"Failed to connect"*: **hold the BOOT button**, press and release **EN/RST**, and keep BOOT pressed until writing starts.
5. When it is done, close the dialog and click **Stop/Restart** (red button). You should see `MicroPython v1.xx ... >>>`.

## Step 3 – Configure and upload the code

1. Open `esp32/config.py` in Thonny and fill in:
   ```python
   WIFI_SSID = "your 2.4 GHz WiFi"
   WIFI_PASSWORD = "your WiFi password"
   AIO_USERNAME = "your Adafruit IO username"
   AIO_KEY = "your Adafruit IO key"
   ```
   Leave `TEMP_FEED` / `LED_FEED` as they are if you used the feed names from step 1.
2. **File → Save as… → MicroPython device** → name it `config.py`.
3. Open `esp32/main.py` → **File → Save as… → MicroPython device** → name it `main.py`.
4. Press **Ctrl+D** (soft reboot) in the Thonny shell. You should see:
   ```
   # connecting to WiFi ...
   TEMP:24.31
   # WiFi connected: 192.168.x.x power save: 0
   # connected to Adafruit IO as <username>
   LED:OFF
   TEMP:27.02
   ```
5. Open your dashboard: the chart fills in every 10 s and the **toggle switches the LED**.
6. Type `ON` or `OFF` in the Thonny shell and press Enter: the LED switches and the dashboard toggle follows.

> `main.py` runs automatically every time the board is powered on.

### Serial protocol (what goes over USB)

| Direction | Line | Meaning |
|---|---|---|
| ESP32 → PC | `TEMP:23.45` | new random temperature (°C) |
| ESP32 → PC | `LED:ON` / `LED:OFF` | LED state after any change |
| ESP32 → PC | `# ...` | info / debug messages for humans |
| PC → ESP32 | `ON` / `OFF` (+ newline) | switch the LED (also accepts `1`/`0`) |

## Step 4 – Free the serial port

**Only one program at a time can use the serial port.** Before starting Node-RED's serial nodes, **close Thonny** (or *Run → Disconnect*). Otherwise Node-RED reports *"Access denied"* / *"port busy"*.

## Step 5 – Node-RED

1. Install the serial nodes (once): in Node-RED **☰ Menu → Manage palette → Install** → `node-red-node-serialport`.
   Or from a terminal: `cd ~/.node-red && npm install node-red-node-serialport`, then restart Node-RED.
2. **☰ Menu → Import** → select `node-red/flow.json` → **Import**. A new tab *ESP32 Exercise 1 (serial + Adafruit IO)* appears.
3. **Serial port**: double-click **ESP32 serial in** → pencil icon next to *ESP32 serial port* → set your port (`COM3`, `/dev/ttyUSB0`, `/dev/cu.SLAB_USBtoUART`…), 115200 baud → *Update*.
4. **Adafruit IO credentials**: double-click **publish esp32-led** → pencil icon next to *Adafruit IO* → **Security** tab → *Username* = your Adafruit IO username, *Password* = your Adafruit IO key → *Update*.
5. **Topics**: in **publish esp32-led**, **esp32-led feed** and **esp32-temperature feed**, replace `YOUR_AIO_USERNAME` with your username (e.g. `mario/feeds/esp32-led`).
6. Click **Deploy**. The serial and MQTT nodes should show **connected**.

### What the flow does

| Nodes | Function |
|---|---|
| **ESP32 serial in** → **parse TEMP / LED** → *temperature*, *LED state* | Reads the serial lines and splits temperature and LED state into separate debug outputs. |
| *raw serial* | Shows every line exactly as received. |
| **LED ON** / **LED OFF** → **ESP32 serial out** | Sends `ON`/`OFF` over the serial port. The LED switches **and** the Adafruit toggle follows. |
| **AIO LED ON** / **AIO LED OFF** → **publish esp32-led** | Publishes `ON`/`OFF` to Adafruit IO. The dashboard toggle and the ESP32 LED both follow. |
| **esp32-led feed**, **esp32-temperature feed** | Subscribe to Adafruit IO and show every new value, from any source. |

Click the square button on the left of an inject node to send its value. In the debug sidebar, set the filter to **all nodes** to see everything.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| No COM port appears | Install the CP210x/CH340 driver; try another (data) USB cable. |
| `WiFi connection failed` / stuck on *connecting* | The ESP32 supports **2.4 GHz only**. On a phone hotspot enable *Maximize compatibility* / 2.4 GHz band. Check SSID/password (case-sensitive). |
| `MQTT connect failed` | Wrong `AIO_USERNAME` / `AIO_KEY` in `config.py` (the username is case-sensitive). |
| Chart stays empty | Feed name in `config.py` differs from the feed **key** on Adafruit IO (Feeds page, *Key* column). |
| Toggle changes but no LED lights up | Your board has no LED on GPIO 2. Set `LED_PIN` in `config.py` to the correct pin, or wire an LED + 220 Ω resistor from GPIO 2 to GND. |
| Toggle reacts after 1–3 s | Normal on phone hotspots and the free Adafruit IO plan. |
| Node-RED: *Access denied* / *port busy* on the serial port | Close Thonny (or any other serial monitor). |
| Thonny can't connect to the board | Node-RED is holding the port: disable the flow or stop Node-RED. |
| Flashing: *Wrong boot mode* | Hold **BOOT** while pressing **EN/RST**, keep holding until writing starts. |
| `ImportError: no module named 'config'` | You forgot to upload `config.py` to the board. |
| Adafruit IO *throttle* warnings | Too many messages: keep `PUBLISH_INTERVAL` ≥ 2 s and don't spam the toggle. |

## Security note

`config.py` with your real key and WiFi password stays **on your board and your PC only**. Don't commit it to a public repository or share it. If your Adafruit IO key leaks, regenerate it from the key icon on io.adafruit.com.

## Exercises to go further

1. Replace the random temperature with a real sensor (e.g. DHT11/DHT22, or the ESP32's internal `esp32.mcu_temperature()`).
2. Add a **Gauge** block on the dashboard for the latest temperature.
3. In Node-RED, switch the LED **ON** automatically when the temperature goes above 28 °C.
4. Add a **slider** feed to change `PUBLISH_INTERVAL` remotely.
