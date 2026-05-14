import socket
import time
import sys

# --- CONFIGURATION ---
# For a 172.20.10.x hotspot, the broadcast address is typically 172.20.10.255
BROADCAST_IP = "172.20.10.255" 
PORT = 1510

def broadcast_trigger(broadcast_ip):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable broadcasting mode
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    print(f"Screaming trigger commands to {broadcast_ip}:{PORT}...")
    
    try:
        # 1. Set a Test Take Name
        test_name = f"Broadcast_Test_{int(time.time())}"
        name_cmd = f'<SetTakeName Name="{test_name}"/>'
        sock.sendto(name_cmd.encode('utf-8'), (broadcast_ip, PORT))
        print(f"Sent: SetTakeName -> {test_name}")
        time.sleep(0.5)
        
        # 2. Start Recording
        sock.sendto("<StartRecording/>".encode('utf-8'), (broadcast_ip, PORT))
        print("Sent: StartRecording")
        print("\nCHECK MOTIVE NOW: Is the record button red? (Recording should last 5 seconds)")
        
        time.sleep(5)
        
        # 3. Stop Recording
        sock.sendto("<StopRecording/>".encode('utf-8'), (broadcast_ip, PORT))
        print("Sent: StopRecording")
        print("\nDone.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    target_broadcast = BROADCAST_IP
    if len(sys.argv) > 1:
        target_broadcast = sys.argv[1]
        
    broadcast_trigger(target_broadcast)
