import psutil
import json
import os
import nmap
from datetime import datetime

class NetMetrics:
    """Class to handle network metrics collection."""

    @staticmethod
    def get_network_metrics():
        """Get network metrics using psutil."""
        network_stats = psutil.net_if_stats()
        network_io = psutil.net_io_counters(pernic=True)
        network_metrics = {}
        for interface, stats in network_stats.items():
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
        """Get IP addresses for all interfaces."""
        addrs = psutil.net_if_addrs()
        ip_addresses = {}
        for interface, addresses in addrs.items():
            for address in addresses:
                if address.family == psutil.AF_INET:
                    ip_addresses[interface] = address.address
        return ip_addresses

    @staticmethod
    def get_connected_devices(local_ip):
        """Get connected devices on the network using nmap."""
        ip_parts = local_ip.split(".")
        network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        nm = nmap.PortScanner()
        nm.scan(hosts=network_range, arguments="-sn")
        devices = []
        for host in nm.all_hosts():
            devices.append({
                "ip": host,
                "hostnames": nm[host].get('hostnames', []),
                "state": nm[host]['status']['state']
            })
        return devices

    @staticmethod
    def log_network_metrics():
        """Log network metrics to a file."""
        network_metrics = NetworkMetrics.get_network_metrics()
        ip_addresses = NetworkMetrics.get_ip_address()
        local_ip = list(ip_addresses.values())[0] if ip_addresses else "Unknown"
        connected_devices = NetworkMetrics.get_connected_devices(local_ip)

        # Combine data
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
