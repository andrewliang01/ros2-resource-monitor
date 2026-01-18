import psutil
import time
import subprocess
import pynvml
import sys
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box


class ROSMonitor:
    def __init__(self):
        self.console = Console()
        self.process_cache = {}

        try:
            pynvml.nvmlInit()
            self.gpu_count = pynvml.nvmlDeviceGetCount()
            self.has_gpu = True
        except Exception:
            self.has_gpu = False

    def get_ros_nodes(self):
        try:
            result = subprocess.run(['ros2', 'node', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                return []
            return [n.strip() for n in result.stdout.split('\n') if n.strip()]
        except FileNotFoundError:
            return []

    def find_pid_by_name(self, node_name):
        clean_name = node_name.lstrip('/')

        # Mapping for nodes where the ROS node name differs significantly
        # from the binary/process name.
        # Example: {"my_ros_node": "python"}
        alias_map = {}

        search_name = alias_map.get(clean_name, clean_name)

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmd_str = ' '.join(proc.info['cmdline'])
                    if search_name in cmd_str:
                        return proc.info['pid']

                if proc.info['name'] and search_name in proc.info['name']:
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def get_process_obj(self, pid):
        if pid not in self.process_cache:
            try:
                self.process_cache[pid] = psutil.Process(pid)
            except psutil.NoSuchProcess:
                return None
        return self.process_cache[pid]

    def get_recursive_usage(self, parent_pid):
        parent = self.get_process_obj(parent_pid)
        if not parent:
            return 0.0, 0.0, 0.0

        try:
            p_cpu = parent.cpu_percent(interval=None)
            p_times = parent.cpu_times()
            total_time = sum(p_times)
            if total_time > 0:
                p_usr = p_cpu * (p_times.user / total_time)
                p_sys = p_cpu * (p_times.system / total_time)
            else:
                p_usr, p_sys = 0, 0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0, 0.0, 0.0

        total_usr = p_usr
        total_sys = p_sys
        total_all = p_cpu

        try:
            children = parent.children(recursive=True)
            for child in children:
                c_obj = self.get_process_obj(child.pid)
                if c_obj:
                    try:
                        c_cpu = c_obj.cpu_percent(interval=None)
                        c_times = c_obj.cpu_times()
                        c_total_time = sum(c_times)

                        if c_total_time > 0:
                            total_usr += c_cpu * (c_times.user / c_total_time)
                            total_sys += c_cpu * (c_times.system / c_total_time)
                        total_all += c_cpu
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return total_usr, total_sys, total_all

    def get_gpu_stats(self, target_pid):
        if not self.has_gpu:
            return "N/A", "N/A"

        pids_to_check = {target_pid}
        try:
            parent = psutil.Process(target_pid)
            for c in parent.children(recursive=True):
                pids_to_check.add(c.pid)
        except:
            pass

        total_mem = 0
        max_util = 0
        found = False

        for i in range(self.gpu_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            for proc_list in [pynvml.nvmlDeviceGetComputeRunningProcesses(handle),
                              pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)]:
                for p in proc_list:
                    if p.pid in pids_to_check:
                        total_mem += p.usedGpuMemory / 1024 / 1024
                        found = True

            if found:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                max_util = max(max_util, util.gpu)

        if found:
            return f"{total_mem:.0f} MB", f"~{max_util}%"
        else:
            return "0 MB", "0%"

    def generate_table(self):
        table = Table(title="ROS 2 Node Resource Monitor", box=box.ROUNDED)
        table.add_column("Node Name", style="cyan", no_wrap=True)
        table.add_column("PID", style="magenta")
        table.add_column("USR %", justify="right", style="green")
        table.add_column("SYS %", justify="right", style="yellow")
        table.add_column("Total %", justify="right", style="bold green")
        if self.has_gpu:
            table.add_column("GPU Mem", justify="right", style="blue")
            table.add_column("GPU Util", justify="right", style="bold blue")

        nodes = self.get_ros_nodes()
        nodes.sort()

        for node_name in nodes:
            pid = self.find_pid_by_name(node_name)

            if pid:
                usr, sys_p, tot = self.get_recursive_usage(pid)
                gpu_mem, gpu_util = self.get_gpu_stats(pid)

                row = [node_name, str(pid), f"{usr:.1f}", f"{sys_p:.1f}", f"{tot:.1f}"]
                if self.has_gpu:
                    row.extend([gpu_mem, gpu_util])
                table.add_row(*row)
            else:
                table.add_row(node_name, "Not Found", "-", "-", "-", "-", "-")

        return table

    def run(self):
        self.console.print("[yellow]Initializing cache (wait for 1st frame)...[/yellow]")
        try:
            with Live(self.generate_table(), refresh_per_second=1, console=self.console) as live:
                while True:
                    time.sleep(1.0)
                    live.update(self.generate_table())
        except KeyboardInterrupt:
            self.console.print("Stopped.")


if __name__ == "__main__":
    monitor = ROSMonitor()
    monitor.run()