import socket
import struct
import time
import sys

# --- CONFIGURATION ---
# Replace with the IP of your Windows machine
MOTIVE_IP = "172.20.10.2"
COMMAND_PORT = 1510

def send_natnet_command(command_str, ip):
    """
    Sends a binary NatNet command packet to Motive.
    Motive 3.x often requires this binary header rather than raw XML.
    """
    # NatNet Packet Header: [MessageID (2 bytes), PacketSize (2 bytes)]
    # Message ID 2 = NAT_REQUEST
    message_id = 2 
    command_bytes = command_str.encode('utf-8') + b'\x00'
    packet_size = len(command_bytes)
    
    # '<HH' means little-endian, two unsigned shorts
    header = struct.pack('<HH', message_id, packet_size)
    packet = header + command_bytes

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        print(f"Sending Binary Command: '{command_str}' to {ip}:{COMMAND_PORT}...")
        sock.sendto(packet, (ip, COMMAND_PORT))
        return True
    except Exception as e:
        print(f"Socket Error: {e}")
        return False
    finally:
        sock.close()

def main():
    target_ip = MOTIVE_IP
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]

    print(f"--- NATNET BINARY TRIGGER TEST ---")
    print(f"Target: {target_ip}")
    
    # 1. Set Take Name
    take_name = f"Binary_Sync_Test_{int(time.time())}"
    send_natnet_command(f'SetTakeName,{take_name}', target_ip)
    time.sleep(0.5)
    
    # 2. Start Recording
    print("Triggering START...")
    send_natnet_command("StartRecording", target_ip)
    
    print("\n--- CHECK MOTIVE NOW ---")
    print("1. Look for a red circle on the Record button.")
    print("2. Check the Message Log at the bottom for '[Command] Received: StartRecording'.")
    
    time.sleep(5)
    
    # 3. Stop Recording
    print("\nTriggering STOP...")
    send_natnet_command("StopRecording", target_ip)
    print("Done.")

if __name__ == "__main__":
    main()
