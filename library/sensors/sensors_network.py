"""
Network-related sensor functions: TCP and UDP port checks, HTTP checks.
"""
import json
import os
import socket
import requests
from library.log import logger


__config = None

def initialize_network(config_file_path: str = "config/nw_config.json") -> bool:
    """ Initialize any Network config . """
    global __config
    if not os.path.exists(config_file_path):
        logger.error(f"Network config file not found: {config_file_path}")
        return False

    with open(config_file_path, "r") as f:
        __config = json.load(f)
        # Initialize SNMP settings from config
        # sensors.snmp_host = __config.get("snmp_host", "localhost")
        # sensors.snmp_community = __config.get("snmp_community", "public")
        # sensors.snmp_port = __config.get("snmp_port", 161)

    return True


def is_port_open_wellknown(service_name: str) -> bool:
    global __config
    """ Check if a TCP port is open for a well-known service from config. """
    if __config is None:
        logger.error("SNMP not initialized. Call initialize_snmp() first.")
        return False
    service_info = __config.get("url checks", {}).get(service_name, None)
    if not service_info:
        logger.error(f"Service name '{service_name}' not found in config.")
        return False
    host = service_info.get("host", "localhost")
    port = service_info.get("port")
    return is_port_open(host, port)
    
    

def is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """ Check if a TCP port is open on a given host. """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        logger.debug(f"Port check failed for {host}:{port} - {e}")
        return False


def is_http_service_available_wellknown(service_name:str) -> bool:
    global __config
    """ Check if a TCP port is open for a well-known service from config. """
    if __config is None:
        logger.error("SNMP not initialized. Call initialize_snmp() first.")
        return False
    service_info = __config.get("url checks", {}).get(service_name, None)
    if not service_info:
        logger.error(f"Service name '{service_name}' not found in config.")
        return False
    url = service_info.get("url", "http://localhost")
    text_to_check = service_info.get("text_to_check", None)
    return is_http_service_available(url, text_to_check=text_to_check)



def is_http_service_available(url: str, timeout: float = 3.0, text_to_check: str = "") -> bool:
    """ Check if an HTTP service is available by sending a GET request. """
    try:
        #disable SSL check
        response = requests.get(url, timeout=timeout, verify=False)
        if response.status_code == 200:
            if text_to_check:
                return text_to_check in response.text
            return True
    except requests.Timeout:
        logger.debug(f"HTTP check timed out for {url}")
    except requests.RequestException as e:
        logger.debug(f"HTTP check failed for {url} - {e}")
    return False


def is_udp_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """ Check if a UDP port is open on a given host. """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b'', (host, port))
        sock.recvfrom(1024)
        return True
    except socket.timeout:
        logger.debug(f"UDP port check timed out for {host}:{port}")
    except OSError as e:
        logger.debug(f"UDP port check failed for {host}:{port} - {e}")
    finally:
        sock.close()
    return False