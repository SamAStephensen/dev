import psutil
import time
import json
import os
import nmap
from datetime import datetime
import platform
import socket
import cpuinfo

# System Metrics Class
class SystemMetrics:
    """Class to handle system metrics collection."""

    @staticmethod
    def get_system_metrics():
        """Get system performance metrics."""
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_times_percent": psutil.cpu_times_percent(interval=1),
            "virtual_memory": psutil.virtual_memory()._asdict(),
            "swap_memory": psutil.swap_memory()._asdict(),
            "disk_usage": psutil.disk_usage('/')._asdict(),
            "disk_partitions": psutil.disk_partitions(),
            "net_io_counters": psutil.net_io_counters()._asdict(),
            "net_if_addrs": psutil.net_if_addrs(),
            "cpu_info": cpuinfo.get_cpu_info(),
            "os_info": platform.platform(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "processes": SystemMetrics.get_process_info()  # Get process-level data
        }
        return system_metrics

    @staticmethod
    def get_process_info():
        """Get information for each process running on the system."""
        processes = []
        
        # Iterate over all PIDs and gather process details
        for pid in psutil.pids():
            try:
                proc = psutil.Process(pid)
                proc_info = {
                    "pid": pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "cpu_percent": proc.cpu_percent(interval=1),
                    "memory_info": proc.memory_info()._asdict(),
                    "open_files": proc.open_files(),
                    "connections": proc.connections(kind='inet'),
                    "exe": proc.exe(),
                    "create_time": datetime.fromtimestamp(proc.create_time()).isoformat(),
                    "user": proc.username()
                }
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue  # Ignore processes that have been terminated or are inaccessible
        
        return processes

    @staticmethod
    def log_system_metrics():
        # Get system metrics
        system_metrics = SystemMetrics.get_system_metrics()

        # Ensure the data folder exists
        if not os.path.exists('data'):
            os.makedirs('data')

        # Write system metrics data to a file
        log_file = f"data/system_metrics_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(system_metrics, f, indent=4)
        
        print(f"System metrics logged to {log_file}")


# Network Metrics Class
class NetworkMetrics:
    """Class to handle network metrics collection."""

    @staticmethod
    def get_network_metrics():
        """Get network metrics using psutil."""
        network_stats = psutil.net_if_stats()
        network_io = psutil.net_io_counters(pernic=True)
        
        network_metrics = {}
        for interface, stats in network_stats.items():
            # Getting statistics for each network interface
            network_metrics[interface] = {
                'is_up': stats.isup,
                'mtu': stats.mtu,
                'bytes_sent': network_io[interface].bytes_sent,
                'bytes_recv': network_io[interface].bytes_recv,
                'packets_sent': network_io[interface].packets_sent,
                'packets_recv': network_io[interface].packets_recv
            }
        
        return network_metrics

    @staticmethod
    def get_ip_address():
        """Get IP address of the machine."""
        addrs = psutil.net_if_addrs()
        ip_addresses = {}
        
        for interface, addresses in addrs.items():
            for address in addresses:
                if address.family == psutil.AF_INET:  # IPv4 address
                    ip_addresses[interface] = address.address
        
        return ip_addresses

    @staticmethod
    def get_connected_devices(local_ip):
        """Get connected devices on the network using nmap."""
        ip_parts = local_ip.split(".")
        network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"  # CIDR range for local subnet
        
        nm = nmap.PortScanner()
        nm.scan(hosts=network_range, arguments="-sn")  # Ping scan (host discovery)
        
        devices = []
        for host in nm.all_hosts():
            if 'hostnames' in nm[host]:
                devices.append({
                    "ip": host,
                    "hostnames": nm[host]['hostnames'],
                    "state": nm[host]['status']['state']
                })
            else:
                devices.append({
                    "ip": host,
                    "hostnames": ["Unknown"],
                    "state": nm[host]['status']['state']
                })
        
        return devices

    @staticmethod
    def log_network_metrics():
        # Get network metrics
        network_metrics = NetworkMetrics.get_network_metrics()
        ip_addresses = NetworkMetrics.get_ip_address()
        
        # Get the local IP address
        local_ip = list(ip_addresses.values())[0] if ip_addresses else "Unknown"
        
        # Get connected devices
        connected_devices = NetworkMetrics.get_connected_devices(local_ip)
        
        # Combine network data
        data = {
            'timestamp': datetime.now().isoformat(),
            'network_metrics': network_metrics,
            'ip_addresses': ip_addresses,
            'connected_devices': connected_devices
        }

        # Ensure the data folder exists
        if not os.path.exists('data'):
            os.makedirs('data')

        # Write network metrics data to a file
        log_file = f"data/network_metrics_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"Network metrics logged to {log_file}")


# Function to run at regular intervals
def run_audit(interval=60):
    while True:
        SystemMetrics.log_system_metrics()  # Log system metrics
        NetworkMetrics.log_network_metrics()  # Log network metrics
        time.sleep(interval)  # Wait for the next interval (default: 60 seconds)

if __name__ == "__main__":
    # Run the system and network audit every minute (60 seconds)
    run_audit(interval=60)
