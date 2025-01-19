import csv
import threading
import time
import os
from pynput import keyboard, mouse
from datetime import datetime
from queue import Queue

# Get the current working directory
current_directory = os.getcwd()

# Define the file path where logs will be saved (in the current directory)
log_file = os.path.join(current_directory, 'input_logs.csv')

# Queue to hold events for later writing
event_queue = Queue()

# A lock to safely write to the file from multiple threads
file_lock = threading.Lock()

# Define the time interval for batching (in seconds)
batch_interval = 0.5  # Write events every 0.5 seconds

# Write events in batches
def write_events_to_file():
    while True:
        # Wait for the batch interval
        time.sleep(batch_interval)

        # Get all events from the queue
        events = []
        while not event_queue.empty():
            events.append(event_queue.get())

        if events:
            # Write the events to the CSV file
            with file_lock:
                with open(log_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    for event in events:
                        writer.writerow(event)

# Initialize the CSV file with a header (if not already present)
def setup_csv():
    try:
        with open(log_file, 'x', newline='') as file:  # 'x' mode creates the file if it doesn't exist
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Event_Type', 'Event_Description', 'Additional_Info'])
    except FileExistsError:
        # If the file exists, we don't need to do anything
        pass

# Function to log events to the queue
def log_event(event_type, event_description, additional_info=""):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    event_queue.put([timestamp, event_type, event_description, additional_info])

# Keyboard listener functions
def on_press(key):
    try:
        log_event('keyboard', f'Key pressed: {key.char}')
    except AttributeError:
        log_event('keyboard', f'Special key pressed: {key}')

def on_release(key):
    if key == keyboard.Key.esc:
        log_event('keyboard', 'Key pressed: ESC - Exiting')
        return False  # Stop listener when ESC is pressed

# Mouse listener functions
def on_move(x, y):
    log_event('mouse', 'Mouse moved', f'({x}, {y})')

def on_click(x, y, button, pressed):
    action = 'pressed' if pressed else 'released'
    log_event('mouse', f'Mouse {action} at', f'({x}, {y}) with {button}')

def on_scroll(x, y, dx, dy):
    log_event('mouse', 'Mouse scrolled', f'({x}, {y}) with delta ({dx}, {dy})')

# Start the CSV setup and batch writer thread
setup_csv()

# Start the event writing thread
batch_writer_thread = threading.Thread(target=write_events_to_file, daemon=True)
batch_writer_thread.start()

# Set up listeners for keyboard and mouse
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)

# Start listeners
keyboard_listener.start()
mouse_listener.start()

# Block the program from exiting
keyboard_listener.join()
mouse_listener.join()
