import time
from system_metrics import SystemMetrics
from network_metrics import NetworkMetrics

def run_audit(interval=60):
    """Run system and network audits at regular intervals."""
    while True:
        SystemMetrics.log_system_metrics()
        NetworkMetrics.log_network_metrics()
        time.sleep(interval)

if __name__ == "__main__":
    run_audit(interval=60)
