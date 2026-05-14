git 
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
        # We don't need a persistent connection for UDP commands
    
    def _send_natnet_command(self, command_str):
        """Sends a binary NatNet command packet to Motive."""
        if not self.ip:
            return False
            
        # Header: [MessageID (2 bytes), PacketSize (2 bytes)]
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
        # Format for Motive 3.x is usually 'SetTakeName,Name'
        return self._send_natnet_command(f'SetTakeName,{name}')

# --- ARGUMENT PARSING ---
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="profile0", help="Aria recording profile (default profile0)")
    parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    parser.add_argument("--aria-ip", required=True, help="IP address of the Aria glasses")
    parser.add_argument("--motive-ip", required=True, help="IP address of the Motive Windows machine")
    return parser.parse_args()

def main():
    args = parse_args()
    take_name = f"Thesis_Sync_{int(time.time())}"
    
    # 1. Initialize Aria SDK
    aria.set_log_level(aria.Level.Info)
    device_client = aria.DeviceClient()
    client_config = aria.DeviceClientConfig()
    client_config.ip_v4_address = args.aria_ip
    device_client.set_client_config(client_config)
    
    # 2. Initialize Motive Control
    motive = MotiveBinaryControl(args.motive_ip)

    # 3. Connect to Aria
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

    print(f"\n--- PREPARING SYNCED TAKE: {take_name} ---")
    
    # Set Motive Take Name
    if motive.set_take_name(take_name):
        print(f"[Motive] Take name set to: {take_name}")
    
    # 4. THE COUNTDOWN
    print("\nREADY FOR RECORDING. PREPARE TO CLAP AT ZERO.")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("!!! START / CLAP NOW !!!\n")

    # 5. START BOTH (Simultaneous Sync Point)
    # Log Unix Timestamps immediately for post-process alignment
    aria_start_ts = time.time()
    recording_manager.start_recording()
    
    motive_start_ts = time.time()
    motive.start_recording()

    # 6. Save Sync Manifest
    sync_data = {
        "take_name": take_name,
        "aria_start_unix": aria_start_ts,
        "motive_start_unix": motive_start_ts,
        "sync_offset_ms": (motive_start_ts - aria_start_ts) * 1000,
        "profile": args.profile,
        "duration_sec": args.duration,
        "aria_ip": args.aria_ip,
        "motive_ip": args.motive_ip
    }
    
    manifest_file = f"{take_name}_sync_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(sync_data, f, indent=4)

    print(f"Recording state: {recording_manager.recording_state}")
    
    # 7. Progress Bar
    try:
        for i in range(args.duration):
            print(f"Recording Progress: {i+1}/{args.duration}s", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nManual stop detected.")

    # 8. STOP BOTH
    print("\n\nStopping recordings...")
    motive.stop_recording()
    recording_manager.stop_recording()

    # Disconnect
    device_client.disconnect(device)
    print(f"\nSUCCESS.")
    print(f"1. Motive Take: '{take_name}'")
    print(f"2. Aria Data: Saved to phone")
    print(f"3. Sync Manifest: '{manifest_file}'")
    print("-" * 30)

if __name__ == "__main__":
    main()
