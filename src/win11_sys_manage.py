import os
import sys
import psutil
import GPUtil
import platform
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import ctypes
import clr  # Import pythonnet module
import json

# Function to check if the script is running with administrative privileges
def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

# Function to elevate to administrative privileges on Windows
def elevate_privileges():
    if not is_admin():
        messagebox.showinfo("Elevation Required", "This script needs to be run with administrative privileges.")
        if sys.platform == "win32":
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        else:
            messagebox.showerror("Unsupported OS", "This script is designed to run on Windows.")

# Load configuration from file
def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as file:
            return json.load(file)
    return {}

# Save configuration to file
def save_config(config):
    with open("config.json", "w") as file:
        json.dump(config, file)

# Function to get the path to OpenHardwareMonitorLib.dll
def get_dll_path():
    config = load_config()
    dll_path = config.get("dll_path", "")
    while not os.path.exists(dll_path):
        dll_path = filedialog.askopenfilename(
            title="Select OpenHardwareMonitorLib.dll",
            filetypes=[("DLL files", "*.dll"), ("All files", "*.*")]
        )
        if dll_path:
            config["dll_path"] = dll_path
            save_config(config)
        else:
            messagebox.showerror("Error", "OpenHardwareMonitorLib.dll is required to run this script.")
            sys.exit(1)
    return dll_path

# Try to add the path to OpenHardwareMonitorLib.dll
try:
    dll_path = get_dll_path()
    clr.AddReference(dll_path)
    from OpenHardwareMonitor.Hardware import Computer
except Exception as e:
    messagebox.showerror("Error", f"Failed to load OpenHardwareMonitorLib.dll: {e}")
    sys.exit(1)

# Function to scan processes and identify resource hogs
def scan_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            p_info = proc.info
            processes.append(p_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

# Function to terminate a selected process
def terminate_process(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()
        messagebox.showinfo("Success", f"Process {pid} terminated successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to terminate process {pid}. Reason: {str(e)}")

# Function to get CPU and GPU temperature using OpenHardwareMonitor
def get_temperatures():
    c = Computer()
    c.CPUEnabled = True
    c.GPUEnabled = True
    c.Open()
    
    cpu_temp = None
    gpu_temp = None

    for i in range(0, len(c.Hardware[0].Sensors)):
        if "temperature" in str(c.Hardware[0].Sensors[i].Identifier).lower():
            cpu_temp = c.Hardware[0].Sensors[i].get_Value()
            break

    for i in range(0, len(c.Hardware[1].Sensors)):
        if "temperature" in str(c.Hardware[1].Sensors[i].Identifier).lower():
            gpu_temp = c.Hardware[1].Sensors[i].get_Value()
            break

    c.Close()

    return cpu_temp, gpu_temp

# Function to get system information
def get_system_info(self, metric=True):
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    gpu_info = GPUtil.getGPUs()[0] if GPUtil.getGPUs() else None
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolution = f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}"
    
    # Fetch CPU and GPU temperatures
    cpu_temp, gpu_temp = get_temperatures()

    if cpu_temp is None:
        cpu_temp = "Unavailable"
    if gpu_temp is None:
        gpu_temp = "Unavailable"

    if isinstance(cpu_temp, float) and not metric:
        cpu_temp = cpu_temp * 9/5 + 32  # Convert to Fahrenheit
    if isinstance(gpu_temp, float) and not metric:
        gpu_temp = gpu_temp * 9/5 + 32  # Convert to Fahrenheit

    info = {
        "CPU Usage (%)": f"{cpu_usage}%",
        "Memory Usage (%)": f"{memory_info.percent}%",
        "Total Memory (GB)": f"{round(memory_info.total / (1024 ** 3), 2)} GB",
        "Available Memory (GB)": f"{round(memory_info.available / (1024 ** 3), 2)} GB",
        "Boot Time": boot_time,
        "Current Time": current_time,
        "Screen Resolution": resolution,
        "CPU Temperature": f"{cpu_temp:.1f}°{'C' if metric else 'F'}" if isinstance(cpu_temp, float) else cpu_temp,
        "CPU Model": platform.processor(),
        "Recommended CPU Temp Range": f"30-70°C" if metric else "86-158°F",
        "GPU Temperature": f"{gpu_temp:.1f}°{'C' if metric else 'F'}" if isinstance(gpu_temp, float) else gpu_temp,
    }

    if gpu_info:
        info["GPU Usage (%)"] = f"{gpu_info.load * 100:.1f}%"
        info["GPU Memory Usage (%)"] = f"{gpu_info.memoryUtil * 100:.1f}%"
        info["GPU Model"] = gpu_info.name
        info["Recommended GPU Temp Range"] = f"30-85°C" if metric else "86-185°F"

    return info

# GUI for displaying processes and system information
class ProcessMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Process Monitor")
        self.geometry("1280x720")
        self.configure(bg='#2e3f4f')
        self.metric = True  # Default to Metric system

        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # System Information Frame
        self.sys_info_frame = ttk.LabelFrame(self, text="System Information", padding=(10, 10))
        self.sys_info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.sys_info_text = tk.Text(self.sys_info_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.sys_info_text.pack(fill=tk.BOTH, expand=True)

        # Process List Frame
        self.proc_frame = ttk.LabelFrame(self, text="Processes", padding=(10, 10))
        self.proc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.proc_frame, columns=("PID", "Name", "CPU %", "Memory %", "User"), show='headings')
        self.tree.heading("PID", text="PID", command=lambda: self.sort_treeview("PID", False))
        self.tree.heading("Name", text="Name", command=lambda: self.sort_treeview("Name", False))
        self.tree.heading("CPU %", text="CPU %", command=lambda: self.sort_treeview("CPU %", False))
        self.tree.heading("Memory %", text="Memory %", command=lambda: self.sort_treeview("Memory %", False))
        self.tree.heading("User", text="User", command=lambda: self.sort_treeview("User", False))
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.tree_scroll = ttk.Scrollbar(self.proc_frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)

        self.terminate_button = tk.Button(self, text="Terminate Process", command=self.terminate_selected_process, bg='#ff4d4d', fg='#ffffff')
        self.terminate_button.pack(pady=10)

        self.refresh_button = tk.Button(self, text="Refresh", command=self.refresh_all, bg='#4caf50', fg='#ffffff')
        self.refresh_button.pack(pady=10)

        self.unit_button = tk.Button(self, text="Toggle Units", command=self.toggle_units, bg='#2196F3', fg='#ffffff')
        self.unit_button.pack(pady=10)

        self.legend_button = tk.Button(self, text="Legend", command=self.show_legend, bg='#ffc107', fg='#ffffff')
        self.legend_button.pack(pady=10)

        self.refresh_all()

    def refresh_all(self):
        self.refresh_sys_info()
        self.refresh_process_list()

    def refresh_sys_info(self):
        self.sys_info_text.config(state=tk.NORMAL)
        self.sys_info_text.delete(1.0, tk.END)
        sys_info = get_system_info(self, self.metric)
        for key, value in sys_info.items():
            self.sys_info_text.insert(tk.END, f"{key}: {value}\n")
        self.sys_info_text.config(state=tk.DISABLED)

    def refresh_process_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        processes = scan_processes()
        for proc in processes:
            color_tag = self.get_process_color(proc['username'])
            self.tree.insert("", "end", values=(proc['pid'], proc['name'], f"{proc['cpu_percent']:.1f}%", f"{proc['memory_percent']:.1f}%", proc['username']), tags=(color_tag,))
        self.tree.tag_configure('system', background='#d3f9d8')
        self.tree.tag_configure('user', background='#d3eaf9')
        self.tree.tag_configure('unknown', background='#f9d3d3')

    def terminate_selected_process(self):
        selected_item = self.tree.selection()
        if selected_item:
            pid = self.tree.item(selected_item[0], "values")[0]
            terminate_process(int(pid))
            self.refresh_process_list()

    def toggle_units(self):
        self.metric = not self.metric
        self.refresh_sys_info()

    def show_legend(self):
        legend_text = ("Legend:\n"
                       "System Processes: Light Green\n"
                       "User Processes: Light Blue\n"
                       "Unknown Processes: Light Red")
        messagebox.showinfo("Legend", legend_text)

    def sort_treeview(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def get_process_color(self, username):
        if username == 'SYSTEM' or 'NT AUTHORITY\SYSTEM' in username:
            return 'system'
        elif username:
            return 'user'
        else:
            return 'unknown'

if __name__ == "__main__":
    if sys.platform == "win32":
        elevate_privileges()
    else:
        messagebox.showerror("Unsupported OS", "This script is designed to run on Windows.")
        sys.exit(1)

    root = ProcessMonitorApp()
    root.mainloop()
