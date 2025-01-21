import csv
import threading
import time
import os
from pynput import keyboard, mouse
from datetime import datetime
from queue import Queue


class InputLogger:
    def __init__(self, directory="data", batch_interval=0.2):
        # Initialize paths and configurations
        self.current_directory = os.getcwd()
        self.log_file = os.path.join(
            self.current_directory, directory, "input_logs.csv"
        )
        self.event_queue = Queue()
        self.file_lock = threading.Lock()
        self.batch_interval = batch_interval
        self.stop_program = False

        # Ensure the log directory exists
        os.makedirs(os.path.join(self.current_directory, directory), exist_ok=True)

        self.setup_csv()

    def setup_csv(self):
        try:
            with open(
                # 'x' mode creates the file if it doesn't exist
                self.log_file, "x", newline=""
            ) as file:  
                writer = csv.writer(file)
                writer.writerow(
                    ["Timestamp", "Event_Type", "Event_Description", "Additional_Info"]
                )
        except FileExistsError:
            pass  

    def log_event(self, event_type, event_description, additional_info=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.event_queue.put(
            [timestamp, event_type, event_description, additional_info]
        )

    def write_events_to_file(self):
        while not self.stop_program:
            time.sleep(self.batch_interval)

            events = []
            while not self.event_queue.empty():
                events.append(self.event_queue.get())

            if events:
                with self.file_lock:
                    with open(self.log_file, "a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerows(events)

    def on_key_press(self, key):
        try:
            self.log_event("keyboard", f"Key pressed: {key.char}")
        except AttributeError:
            self.log_event("keyboard", f"Special key pressed: {key}")

    def on_key_release(self, key):
        try:
            if hasattr(key, "char"):
                self.log_event("keyboard", f"Key released: {key.char}")
            else:
                self.log_event("keyboard", f"Special key released: {key}")
        except Exception as e:
            print(f"Error logging key release: {e}")

        if key == keyboard.Key.esc:
            self.log_event("keyboard", "Key pressed: ESC - Exiting")
            self.stop() 
            return False  # This stops the keyboard listener

    def on_mouse_move(self, x, y):
        self.log_event("mouse", "Mouse moved", f"({x}, {y})")

    def on_mouse_click(self, x, y, button, pressed):
        action = "pressed" if pressed else "released"
        self.log_event("mouse", f"Mouse {action} at", f"({x}, {y}) with {button}")

    def on_mouse_scroll(self, x, y, dx, dy):
        self.log_event("mouse", "Mouse scrolled", f"({x}, {y}) with delta ({dx}, {dy})")

    def stop(self):
        # This method will stop the program by setting stop_program to True
        print("Shutting down...")
        self.stop_program = True
        # Stop both listeners
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def start(self):
        # Start the thread that writes events to file
        writer_thread = threading.Thread(target=self.write_events_to_file, daemon=True)
        writer_thread.start()

        # Create and start the keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press, on_release=self.on_key_release
        )

        # Create and start the mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll,
        )

        try:
            print("Recording keyboard and mouse events. Press ESC to stop...")

            # Start the listeners
            self.keyboard_listener.start()
            self.mouse_listener.start()

            # Block until ESC is pressed (join blocks until the listener stops)
            self.keyboard_listener.join()
            self.mouse_listener.join()

        except Exception as e:
            print(f"Error while running listeners: {e}")
        finally:
            print("Program has stopped.")


# Usage example
if __name__ == "__main__":
    logger = InputLogger()
    logger.start()
