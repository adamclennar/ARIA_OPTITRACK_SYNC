
import argparse
import time
import socket
import json
import aria.sdk as aria

# --- MOTIVE REMOTE CONTROL CLASS ---
class MotiveRemoteControl:
    def __init__(self, ip, port=1510):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_command(self, xml_string):
        if not self.ip:
            # We don't print here to avoid cluttering the countdown
            return
        try:
            self.sock.sendto(xml_string.encode('utf-8'), (self.ip, self.port))
        except Exception as e:
            print(f"\n[Motive] Error sending command: {e}")

    def start_recording(self):
        self.send_command("<StartRecording/>")

    def stop_recording(self):
        self.send_command("<StopRecording/>")

    def set_take_name(self, name):
        self.send_command(f'<SetTakeName Name="{name}"/>')

# --- ARGUMENT PARSING ---
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="profile0", help="Aria recording profile (default profile0)")
    parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    parser.add_argument("--aria-ip", required=True, help="IP address of the Aria glasses")
    parser.add_argument("--motive-ip", default="", help="IP address of the Motive Windows machine")
    return parser.parse_args()

def main():
    args = parse_args()
    take_name = f"Thesis_Capture_{int(time.time())}"
    
    # 1. Initialize Aria
    aria.set_log_level(aria.Level.Info)
    device_client = aria.DeviceClient()
    client_config = aria.DeviceClientConfig()
    client_config.ip_v4_address = args.aria_ip
    device_client.set_client_config(client_config)
    
    # 2. Initialize Motive
    motive = MotiveRemoteControl(args.motive_ip)

    # 3. Connect to Aria
    print(f"[Aria] Connecting to {args.aria_ip}...")
    try:
        device = device_client.connect()
    except Exception as e:
        print(f"Could not connect to Aria: {e}")
        return

    recording_manager = device.recording_manager
    recording_config = aria.RecordingConfig()
    recording_config.profile_name = args.profile
    recording_manager.recording_config = recording_config

    print(f"\n--- PREPARING SYNCED TAKE: {take_name} ---")
    motive.set_take_name(take_name)
    
    # 4. THE COUNTDOWN
    print("\nREADY FOR RECORDING. GET READY TO CLAP.")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("!!! START / CLAP NOW !!!\n")

    # 5. START BOTH (The Sync Point)
    # Capture Unix Timestamps for both
    aria_start_ts = time.time()
    recording_manager.start_recording()
    
    motive_start_ts = time.time()
    motive.start_recording()

    # 6. Save Sync Metadata
    sync_data = {
        "take_name": take_name,
        "aria_start_unix": aria_start_ts,
        "motive_start_unix": motive_start_ts,
        "sync_offset_ms": (motive_start_ts - aria_start_ts) * 1000,
        "profile": args.profile,
        "duration_sec": args.duration
    }
    
    manifest_file = f"{take_name}_sync_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(sync_data, f, indent=4)

    print(f"Recording state: {recording_manager.recording_state}")
    print(f"Recording for {args.duration} seconds...")
    
    # 7. Wait for duration
    # We use a simple progress bar
    for i in range(args.duration):
        print(f"Progress: {i+1}/{args.duration}s", end="\r")
        time.sleep(1)
    print("\n")

    # 8. STOP BOTH
    print("Stopping recordings...")
    motive.stop_recording()
    recording_manager.stop_recording()

    device_client.disconnect(device)
    print(f"Success. Sync manifest saved to {manifest_file}")

if __name__ == "__main__":
    main()
