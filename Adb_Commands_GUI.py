import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk  # Import for Progressbar
import threading
import time


class ADBApp:
    def __init__(self, root):
        self.root = root
        self.logcat_process = None
        self.selected_device = None
        self.setup_gui()

    def setup_gui(self):
        self.root.title("ADB Command Executor")

        # Adjust size
        self.root.geometry("1000x1000")

        # Set minimum window size value
        self.root.minsize(600, 500)

        # Set maximum window size value
        self.root.maxsize(1000, 1000)

        adb_commands = [
            ("List Screen Recording", "adb shell ls /sdcard/movies/*"),
            ("List Screenshots", "adb shell ls /sdcard/Pictures/Screenshots/*"),
            ("List Camera Photos with jpg", "adb shell ls /storage/emulated/0/DCIM/Camera/*.jpg"),
            ("Last Camera Videos with mp4", "adb shell ls /storage/emulated/0/DCIM/Camera/*.mp4"),
            ("List DCIM Camera Photos/Videos", "adb shell ls 'sdcard/DCIM/Camera/*'"),
            ("List Wifi Logs", "adb shell ls /storage/emulated/0/Android/data/com.android.pixellogger/files/logs/wifi_sniffer/*"),
            ("List Audio Logs", "adb shell ls /storage/emulated/0/Android/data/com.android.pixellogger/files/logs/audio_logs/*"),
            ("List Modem Logs", "adb shell ls /storage/emulated/0/Android/data/com.android.pixellogger/files/logs/logs/*"),
            ("Downloaded Cloud Media", "adb shell ls /storage/emulated/0/DCIM/Restored/*"),
            ("Maestro Logs", "adb ls /storage/emulated/0/Android/data/com.google.android.apps.wearables.maestro.companion/files/"),
            ("Generate Bug Report", "adb bugreport"),
            ("Start Logcat", "adb logcat"),
            ("Pull RAMDUMP", "adb pull /data/vendor/ramdump"),
            ("List DCIM Content", "adb shell ls /storage/emulated/0/DCIM")
        ]

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        for label, command in adb_commands:
            btn = tk.Button(button_frame, text=label, command=lambda cmd=command: self.on_command_button_click(cmd))
            btn.pack(fill=tk.X, pady=5)

        self.pull_btn = tk.Button(button_frame, text="Pull Selected Files", command=self.on_pull_files)
        self.pull_btn.pack(fill=tk.X, pady=5)

        self.exit_btn = tk.Button(button_frame, text="Exit", command=self.exit_app)
        self.exit_btn.pack(fill=tk.X, pady=5)

        self.file_list = tk.Listbox(self.root, width=70, height=10, selectmode=tk.MULTIPLE)
        self.file_list.pack(pady=10)

        self.logcat_output = tk.Text(self.root, wrap=tk.NONE, width=70, height=10)
        self.logcat_output.pack(pady=10)

        self.stop_logcat_btn = tk.Button(self.root, text="Stop Logcat", command=self.stop_logcat)
        self.stop_logcat_btn.pack(pady=5)
        self.stop_logcat_btn.pack_forget()  # Initially hide the stop button

        # Progress bar and percentage label
        self.style = ttk.Style(self.root)
        self.style.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate',
                                        style="green.Horizontal.TProgressbar")
        self.progress_label = tk.Label(self.root, text="0%")
        self.progress.pack(pady=10)
        self.progress_label.pack(pady=5)
        self.progress.pack_forget()  # Initially hide the progress bar
        self.progress_label.pack_forget()  # Initially hide the percentage label

    def run_adb_command(self, command):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error executing command: {e}")
            return []

    def check_devices(self):
        devices = self.run_adb_command("adb devices")
        device_list = [line.split()[0] for line in devices if "\tdevice" in line]
        if len(device_list) > 1:
            self.device_selection_window(device_list)
            self.root.wait_window(self.device_selection)  # Wait for device selection
            return self.selected_device
        elif len(device_list) == 1:
            return device_list[0]
        else:
            messagebox.showerror("Error", "No devices connected.")
            return None

    def device_selection_window(self, device_list):
        self.device_selection = tk.Toplevel(self.root)
        self.device_selection.title("Select Device")

        tk.Label(self.device_selection, text="Select a device:").pack(pady=10)

        for device in device_list:
            btn = tk.Button(self.device_selection, text=device, command=lambda d=device: self.set_device(d))
            btn.pack(fill=tk.X, pady=5)

    def set_device(self, device):
        self.selected_device = device
        self.device_selection.destroy()

    def execute_command(self, command):
        device = self.check_devices()
        if device:
            command = f"adb -s {device} " + command.split("adb ", 1)[1]  # Adjust command to specify the device
            files = self.run_adb_command(command)
            if files:
                self.file_list.delete(0, tk.END)
                for file in files:
                    self.file_list.insert(tk.END, file)
            else:
                messagebox.showinfo("Info", "No files found.")

    def on_command_button_click(self, command):
        if command == "adb bugreport":
            self.run_bugreport()
        elif command == "adb logcat":
            self.start_logcat()
        else:
            self.execute_command(command)

    def on_pull_files(self):
        selected_files_indices = self.file_list.curselection()
        if selected_files_indices:
            device = self.check_devices()
            if device:
                total_files = len(selected_files_indices)
                self.progress["maximum"] = total_files
                self.progress["value"] = 0
                self.progress.pack()  # Show the progress bar
                self.progress_label.pack()  # Show the percentage label

                for index, file_index in enumerate(selected_files_indices):
                    file_to_pull = self.file_list.get(file_index)
                    subprocess.run(["adb", "-s", device, "pull", file_to_pull])

                    # Update the progress bar and percentage label
                    self.progress["value"] = index + 1
                    percentage = int(((index + 1) / total_files) * 100)
                    self.progress_label.config(text=f"{percentage}%")
                    self.root.update_idletasks()  # Ensure the GUI updates

                messagebox.showinfo("Info", "Selected files pulled successfully.")
                self.progress.pack_forget()  # Hide the progress bar after completion
                self.progress_label.pack_forget()  # Hide the percentage label
        else:
            messagebox.showwarning("Warning", "No files selected to pull.")

    def run_bugreport(self):
        self.progress["maximum"] = 100
        self.progress["value"] = 0
        self.progress.pack()  # Show the progress bar
        self.progress_label.pack()  # Show the percentage label

        for i in range(1, 101):  # Increment by 1% each loop
            time.sleep(0.05)  # Simulate some time for each step
            self.progress["value"] = i
            self.progress_label.config(text=f"{i}%")
            self.root.update_idletasks()  # Ensure the GUI updates

        result = self.run_adb_command("adb bugreport")
        if result:
            self.file_list.delete(0, tk.END)
            for line in result:
                self.file_list.insert(tk.END, line)
        else:
            messagebox.showinfo("Info", "Bug report generated.")

        self.progress.pack_forget()  # Hide the progress bar after completion
        self.progress_label.pack_forget()  # Hide the percentage label

    def start_logcat(self):
        self.logcat_output.delete(1.0, tk.END)  # Clear previous logs

        # Show the stop logcat button
        self.stop_logcat_btn.pack(pady=5)

        # Start logcat in a separate thread
        self.logcat_thread = threading.Thread(target=self.run_logcat, daemon=True)
        self.logcat_thread.start()

    def run_logcat(self):
        device = self.check_devices()
        if device:
            self.logcat_process = subprocess.Popen(f"adb -s {device} logcat", shell=True, stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE, text=True)
            while True:
                if self.logcat_process.poll() is not None:
                    break
                line = self.logcat_process.stdout.readline()
                if line:
                    self.logcat_output.insert(tk.END, line)
                    self.logcat_output.yview(tk.END)
                time.sleep(0)  # Add a small delay to prevent high CPU usage

    def stop_logcat(self):
        if self.logcat_process:
            self.logcat_process.terminate()
            self.logcat_process.wait()
            filename = simpledialog.askstring("Save File", "Enter filename to save logs (e.g., log.txt):")
            if filename and not filename.endswith(".txt"):
                filename += ".txt"
            if filename:
                with open(filename, "w") as file:
                    file.write(self.logcat_output.get(1.0, tk.END))
                messagebox.showinfo("Info", f"Logs saved to {filename}")

        # Hide the stop logcat button
        self.stop_logcat_btn.pack_forget()

    def exit_app(self):
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = ADBApp(root)
    root.mainloop()
