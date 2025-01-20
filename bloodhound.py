import psutil
import socket
import datetime
import time
import logging
import subprocess
import json
import os

# Setup logging to capture any critical information
logging.basicConfig(filename='system_monitor.log', level=logging.DEBUG)

def get_cpu_info():
    """Get CPU usage information."""
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=False)
    return {'cpu_percent': cpu_percent, 'cpu_count': cpu_count}

def get_memory_info():
    """Get memory usage information."""
    memory = psutil.virtual_memory()
    return {
        'total_memory': memory.total,
        'used_memory': memory.used,
        'available_memory': memory.available,
        'memory_percent': memory.percent
    }

def get_disk_info():
    """Get disk usage information."""
    disk = psutil.disk_usage('/')
    return {
        'total_disk': disk.total,
        'used_disk': disk.used,
        'free_disk': disk.free,
        'disk_percent': disk.percent
    }

def get_network_info():
    """Get network interface information."""
    network_info = {}
    for interface, addrs in psutil.net_if_addrs().items():
        network_info[interface] = {
            'ipv4': [addr.address for addr in addrs if addr.family == psutil.AF_INET],
            'ipv6': [addr.address for addr in addrs if addr.family == psutil.AF_INET6]
        }
    return network_info

def get_battery_info():
    """Get battery information."""
    battery = psutil.sensors_battery()
    if battery:
        return {
            'battery_percent': battery.percent,
            'plugged_in': battery.power_plugged,
            'time_left': battery.secsleft / 60 if battery.secsleft != psutil.POWER_TIME_UNLIMITED else 'Unlimited'
        }
    return None

def get_temperature_info():
    """Get CPU temperature information."""
    try:
        temperature_info = psutil.sensors_temperatures()
        return temperature_info
    except AttributeError:
        return None  # Not available on all systems

def get_process_info():
    """Get information about running processes."""
    process_info = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        process_info.append(proc.info)
    return process_info

def get_system_uptime():
    """Get the system uptime."""
    uptime_seconds = psutil.boot_time()
    uptime = datetime.datetime.fromtimestamp(uptime_seconds)
    return uptime

def get_disk_io_stats():
    """Get disk I/O stats."""
    disk_io = psutil.disk_io_counters()
    return {
        'read_count': disk_io.read_count,
        'write_count': disk_io.write_count,
        'read_bytes': disk_io.read_bytes,
        'write_bytes': disk_io.write_bytes
    }

def get_system_logs():
    """Collect basic system logs."""
    logs = []
    try:
        logs.append(subprocess.getoutput("dmesg"))
    except Exception as e:
        logging.error(f"Error fetching system logs: {e}")
    return logs

# Collect all the system data into a dictionary
def collect_system_info():
    system_info = {}
    system_info['cpu'] = get_cpu_info()
    system_info['memory'] = get_memory_info()
    system_info['disk'] = get_disk_info()
    system_info['network'] = get_network_info()
    system_info['battery'] = get_battery_info()
    system_info['temperature'] = get_temperature_info()
    system_info['processes'] = get_process_info()
    system_info['uptime'] = get_system_uptime()
    system_info['disk_io'] = get_disk_io_stats()
    system_info['logs'] = get_system_logs()

    return system_info

# Save the data to a new file with a timestamp
def save_to_file(data):
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Create a new file name using the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"data/system_info_{timestamp}.json"
    
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)

    logging.info(f"System data saved to {file_name}")

# Run the data collection at intervals
def run_system_monitor(interval_seconds=3600):
    while True:
        try:
            system_info = collect_system_info()
            save_to_file(system_info)
            print(f"System info saved at {datetime.datetime.now()}")
            time.sleep(interval_seconds)  # Sleep for the specified interval (e.g., 1 hour)
        except Exception as e:
            logging.error(f"Error occurred: {e}")
            time.sleep(60)  # Sleep for 1 minute before retrying

if __name__ == "__main__":
    run_system_monitor(interval_seconds=3600)  # Collect and save every 1 hour (3600 seconds)
