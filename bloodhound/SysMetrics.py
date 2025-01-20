import psutil
import json
import os
import platform
import socket
import cpuinfo
from datetime import datetime

class SysMetrics:
    """Class to handle system metrics collection."""

    @staticmethod
    def get_system_metrics():
        """Get system performance metrics."""
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_times_percent": psutil.cpu_times_percent(interval=1)._asdict(),
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
            "processes": SystemMetrics.get_process_info()
        }
        return system_metrics

    @staticmethod
    def get_process_info():
        """Get information for each process running on the system."""
        processes = []
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
                continue
        return processes

    @staticmethod
    def log_system_metrics():
        """Log system metrics to a file."""
        system_metrics = SystemMetrics.get_system_metrics()

        # Ensure the data folder exists
        if not os.path.exists('data'):
            os.makedirs('data')

        # Write system metrics data to a file
        log_file = f"data/system_metrics_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(system_metrics, f, indent=4)

        print(f"System metrics logged to {log_file}")
