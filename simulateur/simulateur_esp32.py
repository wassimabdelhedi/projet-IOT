import sys
# Force l'encodage UTF-8 pour le terminal Windows (nécessaire pour les icônes)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Pour les versions plus anciennes de Python
        pass

import paho.mqtt.client as mqtt
import json, time, random

# ── CONFIG ──────────────────────────────────────
BROKER    = "localhost"    
PORT      = 1883
# ID unique pour éviter les conflits et déconnexions
CLIENT_ID = f"esp32-sem-sim-{random.randint(100, 999)}"

T_SENSOR  = "sem/bat1/node1/sensors/power"
T_CMD     = "sem/bat1/node1/cmd/relay"
T_STATUS  = "sem/bat1/node1/status/alive"

SEUIL_W   = 300.0
VOLTAGE   = 230.0   # Tension nominale réseau européen (EN 50160)

# ── ÉTAT ────────────────────────────────────────
relay_on  = True
power_val = 80.0
direction = 1
step      = 0

# ── CALLBACKS ───────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MQTT] Connecté au broker {BROKER}")
        client.subscribe(T_CMD, qos=1)
        print(f"[MQTT] Abonné à : {T_CMD}")
    else:
        print(f"[MQTT] Échec connexion, code: {reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"[MQTT] Déconnecté (code={reason_code}) — reconnexion auto...")

def on_message(client, userdata, msg):
    global relay_on
    cmd = msg.payload.decode().strip()
    print(f"\n[CMD] Reçu sur {msg.topic} : {cmd}")
    if cmd == "0":
        relay_on = False
        print("[RELAY] → OUVERT — charge coupée ⚡")
    elif cmd == "1":
        relay_on = True
        print("[RELAY] → FERMÉ — charge rétablie ✓")

# ── SCÉNARIO ────────────────────────────────────
def next_power():
    global power_val, direction, step
    step += 1

    # Variation aléatoire
    delta = random.uniform(8, 18) * direction
    power_val += delta

    # Bornes de simulation
    if power_val >= 380:
        direction = -1
    if power_val <= 50:
        direction = 1

    # Forcer un dépassement tous les 20 cycles
    if step % 20 == 0:
        power_val = 320.0
        direction = -1
        print("\n>>> SIMULATION : Dépassement du seuil forcé <<<\n")

    return round(power_val, 1)

def main():
    global relay_on

    print("=" * 45)
    print("  Smart Energy Monitoring — Simulateur ESP32")
    print("=" * 45)
    print(f"  Broker  : {BROKER}:{PORT}")
    print(f"  Topic   : {T_SENSOR}")
    print(f"  Seuil   : {SEUIL_W} W")
    print(f"  Interval: 5 secondes")
    print("=" * 45)
    print("  Ctrl+C pour arrêter\n")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID
    )
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    print("[MQTT] Connexion en cours...")
    try:
        client.connect(BROKER, PORT, keepalive=60)
    except Exception as e:
        print(f"[ERREUR] Connexion impossible : {e}")
        return

    client.loop_start()
    time.sleep(1.5)

    pub_count = 0

    try:
        while True:
            if not client.is_connected():
                time.sleep(1)
                continue

            power   = next_power()
            # Légère variation de tension ±5V autour de 230V (réaliste réseau EU)
            voltage = round(230.0 + random.uniform(-5, 5), 1)
            current = round(power / voltage, 2)

            # Logique de protection locale (Délestage)
            if power > SEUIL_W and relay_on:
                print(f"[SEUIL] {power}W > {SEUIL_W}W → coupure locale")
                relay_on = False

            payload = {
                "node_id"   : CLIENT_ID,
                "power_W"   : power,
                "current_A" : current,
                "voltage_V" : voltage,
                "relay"     : 1 if relay_on else 0,
                "seuil_ok"  : 1 if power <= SEUIL_W else 0,
                "ts"        : time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

            result = client.publish(T_SENSOR, json.dumps(payload), qos=1)

            pub_count += 1
            status    = "✓" if result.rc == 0 else "✗"
            relay_str = "ON  ✓" if relay_on else "OFF ⚡"
            alert     = "  ⚠️  SURCHARGE" if power > SEUIL_W else ""

            # Affichage formaté exactement comme demandé
            print(f"[{pub_count:03d}] {status}  "
                  f"P={power:6.1f}W  "
                  f"V={voltage:5.1f}V  "
                  f"I={current:.2f}A  "
                  f"relay={relay_str}"
                  f"{alert}")

            # Heartbeat toutes les 30s
            if pub_count % 6 == 0:
                client.publish(T_STATUS, json.dumps({"alive": True}))

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[INFO] Arrêt du simulateur.")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
