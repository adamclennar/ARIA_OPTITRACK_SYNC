import socket
import time
import sys

# --- CONFIGURATION ---
# Replace this with the IP address of your Windows machine running Motive
MOTIVE_IP = "127.0.0.1" 
PORT = 1510

def test_motive(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"Testing Motive Trigger on {ip}:{PORT}...")
    
    # 1. Set Take Name
    test_name = f"Connection_Test_{int(time.time())}"
    name_cmd = f'<SetTakeName Name="{test_name}"/>'
    try:
        sock.sendto(name_cmd.encode('utf-8'), (ip, PORT))
        print(f"Sent: SetTakeName -> {test_name}")
        time.sleep(0.5)
        
        # 2. Start Recording
        sock.sendto("<StartRecording/>".encode('utf-8'), (ip, PORT))
        print("Sent: StartRecording")
        print("\nCHECK MOTIVE NOW: Is the record button red? (Recording should last 5 seconds)")
        
        time.sleep(5)
        
        # 3. Stop Recording
        sock.sendto("<StopRecording/>".encode('utf-8'), (ip, PORT))
        print("Sent: StopRecording")
        print("\nDone. Check the Data pane in Motive for the new take.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    target_ip = MOTIVE_IP
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]
    
    if target_ip == "127.0.0.1" and len(sys.argv) <= 1:
        print("Error: No IP address provided.")
        print("Usage: python3 test_motive_trigger.py [WINDOWS_MOTIVE_IP]")
    else:
        test_motive(target_ip)
