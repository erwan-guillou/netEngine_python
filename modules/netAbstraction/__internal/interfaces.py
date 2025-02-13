
import netifaces
import socket

def GetAdapterList() -> list[str]:
    result = []
    interfaces = netifaces.interfaces() 
    for interface in interfaces:
        addrs = netifaces.ifaddresses(str(interface))
        if netifaces.AF_INET in addrs:
            result.append(interface)
    return result

def GetAdapterAddress(intf:str) -> str:
    addrs = netifaces.ifaddresses(intf)
    if netifaces.AF_INET in addrs:
        return addrs[netifaces.AF_INET][0]['addr']
    return ""

def GetBroadcastAddress(intf:str) -> str:
    addrs = netifaces.ifaddresses(intf)
    if netifaces.AF_INET in addrs:
        return addrs[netifaces.AF_INET][0]['broadcast']
    return ""

def GetLocalIpFromServer(server_ip:str) -> str|None:
    """Find the client's local IP address used to reach the given server IP."""
    try:
        # Create a temporary UDP socket
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_sock.connect((server_ip, 80))  # Doesn't actually send data
        client_ip = temp_sock.getsockname()[0]  # Get the client's IP on this interface
        temp_sock.close()
        return client_ip
    except Exception as e:
        print(f"Error determining client IP: {e}")
        return None