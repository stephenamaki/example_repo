import os
import subprocess
import time
from datetime import datetime

# Dictionary mapping VLAN interfaces to VRRP group names
vlan_vrrp_mapping = {
    "Vlan220": "220",  # VLAN 220 example (active)
    # "Vlan221": "221",  # VLAN 221 example (commented out)
    # "Vlan222": "222",  # VLAN 222 example (commented out)
}

# Target host
target_host = "3.3.3.3"

# Source interface (change this to the desired source interface)
source_interface = "Vlan4094"

# Log file settings
log_file_path = "track_log.txt"
max_log_size_bytes = 1048576  # 1 MB

# Function to change VRRP priority for a VLAN interface
def change_priority(interface, priority):
    vrrp_group = vlan_vrrp_mapping.get(interface)
    if vrrp_group is not None:
        print("Changing VRRP priority to {} in {}...".format(priority, interface))
        subprocess.call(["FastCli", "-p", "15", "-c", "conf t\ninterface {}\nvrrp {} priority-level {}\nend".format(interface, vrrp_group, priority)])
    else:
        print("Error: No VRRP group found for {}".format(interface))

# Function to rotate log file
def rotate_log_file():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archived_log_file_path = "monitoring_log_{}.txt".format(timestamp)
    os.rename(log_file_path, archived_log_file_path)
    print("Log file rotated. Archived log file: {}".format(archived_log_file_path))
    with open(log_file_path, "w"):
        pass  # Create a new empty log file

# Continuous monitoring
print("Starting continuous monitoring...")
preemption = False
while True:
    # Check log file size
    if os.path.isfile(log_file_path) and os.path.getsize(log_file_path) >= max_log_size_bytes:
        rotate_log_file()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Perform ping test with source interface
    subprocess.call(["FastCli", "-p", "15", "-c", "ping {} source {}".format(target_host, source_interface)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Perform ping test
    if subprocess.Popen(["ping", "-c", "1", target_host], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].find("1 packets transmitted, 1 received, 0% packet loss") != -1:
        log_message = "{}: Ping successful\n".format(timestamp)
        if os.path.isfile(log_file_path):
            with open(log_file_path, "a") as log_file:
                log_file.write(log_message)
        print(log_message)
        if preemption:
            for interface in vlan_vrrp_mapping.keys():
                change_priority(interface, "150")  # Restore priority to 150
            preemption = False  # Reset preemption flag
    else:
        log_message = "{}: Ping failed. Initiating VRRP priority change...\n".format(timestamp)
        if os.path.isfile(log_file_path):
            with open(log_file_path, "a") as log_file:
                log_file.write(log_message)
        print(log_message)
        for interface in vlan_vrrp_mapping.keys():
            change_priority(interface, "1")  # Set priority to 1
        preemption = True  # Set preemption flag
    time.sleep(1)