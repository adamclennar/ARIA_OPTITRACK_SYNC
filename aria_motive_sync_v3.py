
import argparse
import time
import socket
import struct
import json
import aria.sdk as aria

# --- MOTIVE BINARY CONTROL CLASS ---
class MotiveBinaryControl:
    def __init__(self, ip, port=1510):
        self.ip = ip
        self.port = port
    
    def _send_natnet_command(self, command_str):
        """Sends a binary NatNet command packet to Motive."""
        if not self.ip:
            return False
            
        # Message ID 2 = NAT_REQUEST
        message_id = 2 
        command_bytes = command_str.encode('utf-8') + b'\x00'
        packet_size = len(command_bytes)
        
        header = struct.pack('<HH', message_id, packet_size)
        packet = header + command_bytes

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(packet, (self.ip, self.port))
            return True
        except Exception as e:
            print(f"\n[Motive] Network Error: {e}")
            return False
        finally:
            sock.close()

    def start_recording(self):
        return self._send_natnet_command("StartRecording")

    def stop_recording(self):
        return self._send_natnet_command("StopRecording")

    def set_take_name(self, name):
        # Format for Motive 3.x
        return self._send_natnet_command(f'SetTakeName,{name}')

# --- MAIN EXECUTION ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="profile0", help="Aria recording profile")
    parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    parser.add_argument("--aria-ip", required=True, help="IP address of the Aria glasses")
    parser.add_argument("--motive-ip", required=True, help="IP address of the Motive Windows machine")
    args = parser.parse_args()

    # Generate a unique take name
    take_name = f"Thesis_Sync_v3_{int(time.time())}"
    
    # 1. Initialize Aria SDK
    aria.set_log_level(aria.Level.Info)
    device_client = aria.DeviceClient()
    client_config = aria.DeviceClientConfig()
    client_config.ip_v4_address = args.aria_ip
    device_client.set_client_config(client_config)
    
    # 2. Connect to Aria
    print(f"[Aria] Connecting to {args.aria_ip}...")
    try:
        device = device_client.connect()
    except Exception as e:
        print(f"FAILED to connect to Aria: {e}")
        return

    recording_manager = device.recording_manager
    recording_config = aria.RecordingConfig()
    recording_config.profile_name = args.profile
    recording_manager.recording_config = recording_config

    # 3. Start Aria "Warm-up"
    print(f"[Aria] Starting recording initialization (Warm-up)...")
    recording_manager.start_recording()

    # 4. Wait for Aria to reach 'Recording' state
    # This handles the ~15 second delay automatically
    start_wait_time = time.time()
    while recording_manager.recording_state != aria.RecordingState.Recording:
        elapsed = int(time.time() - start_wait_time)
        print(f"  Waiting for Aria sensors to stabilize... ({elapsed}s)", end="\r")
        time.sleep(0.5)
    
    print(f"\n[Aria] Sensors READY. Initialization took {int(time.time() - start_wait_time)}s.")

    # 5. Initialize Motive Control
    motive = MotiveBinaryControl(args.motive_ip)
    if motive.set_take_name(take_name):
        print(f"[Motive] Take name set to: {take_name}")

    # 6. THE SYNC COUNTDOWN
    print("\n--- PREPARING SYNC TRIGGER ---")
    print("Motive will start at the end of this countdown.")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    # 7. TRIGGER MOTIVE AT "ZERO" (The Sync Point)
    # Log Unix Timestamp immediately for alignment
    motive_trigger_ts = time.time()
    motive.start_recording()
    print("!!! START / CLAP NOW !!!\n")

    # 8. Save Sync Metadata
    sync_data = {
        "take_name": take_name,
        "motive_start_unix": motive_trigger_ts,
        "duration_sec": args.duration,
        "profile": args.profile,
        "note": "Aria was already recording when Motive was triggered at motive_start_unix."
    }
    
    manifest_file = f"{take_name}_sync_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(sync_data, f, indent=4)

    # 9. Recording Duration Progress
    try:
        for i in range(args.duration):
            print(f"Synced Recording Progress: {i+1}/{args.duration}s", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nManual stop detected.")

    # 10. STOP BOTH
    print("\n\nStopping recordings...")
    motive.stop_recording()
    recording_manager.stop_recording()

    # 11. Disconnect
    device_client.disconnect(device)
    print(f"\nSUCCESS.")
    print(f"1. Motive Take: '{take_name}'")
    print(f"2. Aria Sync Manifest: '{manifest_file}'")
    print(f"   (Alignment point is exactly at Unix: {motive_trigger_ts})")
    print("-" * 30)

if __name__ == "__main__":
    main()
