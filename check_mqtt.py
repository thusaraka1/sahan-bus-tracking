import time
import ssl
import json
import paho.mqtt.client as mqtt

brokers = [
    {
        "name": "Primary Broker (.env)",
        "host": "b5ad82f71b0d40d6bcf02b00ce1cd933.s1.eu.hivemq.cloud",
        "port": 8883,
        "user": "Bus_track",
        "pass": "Bus@12345"
    },
    {
        "name": "Lee Bus Broker",
        "host": "9ce9a991c31542a49529dd4db804495d.s1.eu.hivemq.cloud",
        "port": 8883,
        "user": "lee_project",
        "pass": "Lee_project@123"
    }
]

messages_received = []

def make_on_connect(broker_name):
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[{broker_name}] Connected successfully! Subscribing to '#'...")
            client.subscribe("#", qos=1)
        else:
            print(f"[{broker_name}] Connection failed with code {rc}")
    return on_connect

def make_on_message(broker_name):
    def on_message(client, userdata, msg):
        payload_str = msg.payload.decode('utf-8', errors='replace')
        item = {
            "broker": broker_name,
            "topic": msg.topic,
            "time": time.strftime('%H:%M:%S'),
            "payload": payload_str
        }
        messages_received.append(item)
        print(f"\n>>> [{item['time']}] RECEIVED MESSAGE ON [{broker_name}]")
        print(f"    Topic: {msg.topic}")
        print(f"    Payload: {payload_str}")
    return on_message

clients = []
print("Initializing MQTT clients and connecting over TLS...")
for b in brokers:
    try:
        client_id = f"diagnostic_{int(time.time())}_{b['name'][:6].replace(' ', '_')}"
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        c.username_pw_set(b["user"], b["pass"])
        c.tls_set(tls_version=ssl.PROTOCOL_TLS)
        c.on_connect = make_on_connect(b["name"])
        c.on_message = make_on_message(b["name"])
        print(f"Connecting to {b['name']} ({b['host']}:{b['port']})...")
        c.connect(b["host"], b["port"], keepalive=30)
        c.loop_start()
        clients.append(c)
    except Exception as e:
        print(f"Failed to setup {b['name']}: {e}")

listen_duration = 30
print(f"\nMonitoring all MQTT topics for {listen_duration} seconds...")
for i in range(listen_duration):
    time.sleep(1)
    if (i + 1) % 5 == 0:
        print(f"  ...listening ({i + 1}/{listen_duration}s elapsed, {len(messages_received)} messages captured so far)")

print("\nStopping listeners...")
for c in clients:
    c.loop_stop()
    c.disconnect()

print("\n" + "=" * 60)
print(f"SUMMARY: Total live messages captured: {len(messages_received)}")
if messages_received:
    print("LIVE DATA IS CURRENTLY ACTIVE! Messages received:")
    for idx, m in enumerate(messages_received, 1):
        print(f"\n[{idx}] Time: {m['time']} | Broker: {m['broker']}")
        print(f"    Topic: {m['topic']}")
        print(f"    Data: {m['payload']}")
else:
    print("NO LIVE DATA RECEIVED in the last 30 seconds.")
    print("Broker connection was successful, but no device is actively publishing right now.")
print("=" * 60)
