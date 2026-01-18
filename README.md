# ROS 2 Resource Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)

[中文文档](#chinese-doc) | [English Documentation](#english-doc)

---
<a name="chinese-doc"></a>
## ROS 2 资源监控器

一个专为 **ROS 2** 开发者设计的轻量级终端资源监控工具。

**痛点解决**：标准的系统监控工具（如 `htop` 或 `nvtop`）通常只显示进程的可执行文件名（如 `python` 或 `ros2`），导致开发者难以区分具体的 ROS 节点。**ROS 2 Resource Monitor** 填补了这一空白，它能自动将 `ros2 node list` 中的节点名映射到系统 PID，并提供递归的 CPU 和 GPU 统计。

![Demo](https://via.placeholder.com/800x400?text=Placeholder+for+Screenshot+of+r2mon)
*(建议在此处替换为你的运行截图)*

### ✨ 核心特性

* 🔍 **节点-进程自动映射**：自动寻找 ROS 2 节点名对应的系统主 PID。
* 🌲 **递归 CPU 统计**：准确计算节点及其**所有子进程**的 CPU 总占用。完美解决 Python 脚本（作为启动器）启动繁重计算子进程时，主进程 CPU 显示为 0% 的问题。
* 📊 **详细 CPU 分解**：将 CPU 占用分解为 **USR**（用户态）和 **SYS**（内核态），帮助快速定位是计算瓶颈还是 IO/通信瓶颈。
* 🎮 **NVIDIA GPU 支持**：集成 `pynvml`，实时追踪每个节点的显存 (VRAM) 使用量和 GPU 算力利用率。
* ⚡ **无闪烁界面**：基于 `rich` 库构建，提供流畅、现代化的终端 UI 体验。

### 📦 依赖项

* ROS 2 (运行前请 source 环境变量)
* Python 3
* NVIDIA Driver (可选，用于 GPU 统计)

```bash
pip install psutil pynvml rich
```

### 🚀 安装与使用

1. **克隆仓库**：
```bash
git clone https://github.com/andrewliang01/ros2-resource-monitor.git
cd ros2-resource-monitor
```


2. **运行监控器** (确保已 source ROS 2 环境)：
```bash
# 例如: source /opt/ros/humble/setup.bash
python3 ros_monitor.py
```



### ⚙️ 进阶配置 (处理特殊进程名)

默认情况下，工具会在进程的命令行参数或可执行文件名中搜索节点名。

如果你的节点名与进程名差异巨大（例如：节点名叫 `my_algo_node`，但运行在通用的 `python` 进程中且没有显式参数），你可以在 `ros_monitor.py` 的 `find_pid_by_name` 方法中手动添加映射：

```python
def find_pid_by_name(self, node_name):
    # ...
    alias_map = {
        "pointcloud2heightscan_node": "dlio_heightscan_node",
        "mujoco_simulator": "python"  # 尝试匹配 python 进程
    }
    # ...

```

### 📊 指标说明

| 列名 | 说明 |
| --- | --- |
| **Node Name** | `ros2 node list` 返回的节点名称。 |
| **Main PID** | 该节点对应的主进程 ID。 |
| **USR %** | 用户态 CPU 占用（应用程序逻辑、计算）。 |
| **SYS %** | 内核态 CPU 占用（系统调用、驱动、数据拷贝）。**过高的 SYS% (>30%) 通常意味着过多的数据序列化或通信开销。** |
| **Total %** | USR 和 SYS 的总和。100% 代表跑满一个 CPU 核心。包含所有子进程的递归统计。 |
| **GPU Mem** | 该进程树占用的显存大小。 |
| **GPU Util** | GPU 计算单元的近似利用率。 |

---

<a name="english-doc"></a>
## ROS 2 Resource Monitor

A lightweight, TUI-based resource monitor specifically designed for **ROS 2**.

**The Problem**: Standard tools like `htop` or `nvtop` show processes by executable name, making it difficult to distinguish between multiple ROS nodes (especially Python-based ones). **ROS 2 Resource Monitor** bridges this gap by mapping `ros2 node list` directly to system PIDs, recursive CPU usage, and GPU statistics.

### ✨ Features

* 🔍 **Node-to-Process Mapping**: Automatically finds the PID corresponding to a ROS 2 node name.
* 🌲 **Recursive CPU Accounting**: Correctly calculates CPU usage for nodes that spawn child processes (e.g., Python scripts spawning heavy computation threads), solving the "0% CPU" issue for wrapper scripts.
* 📊 **Detailed CPU Breakdown**: Splits CPU usage into **USR** (User space) and **SYS** (Kernel space) to help diagnose I/O bottlenecks vs. Computational bottlenecks.
* 🎮 **NVIDIA GPU Support**: Tracks Video Memory (VRAM) and Compute Utilization for each node (via `pynvml`).
* ⚡ **Zero-Flicker Interface**: Uses `rich` library for a smooth, modern terminal UI.

### 📦 Dependencies

* ROS 2 (Source your environment before running)
* Python 3
* NVIDIA Driver (Optional, for GPU stats)

```bash
pip install psutil pynvml rich
```

### 🚀 Installation & Usage

1. **Clone the repository**:
```bash
git clone https://github.com/andrewliang01/ros2-resource-monitor.git
cd ros2-resource-monitor
```


2. **Run the monitor** (Ensure ROS 2 environment is sourced):
```bash
# Example: source /opt/ros/humble/setup.bash
python3 ros_monitor.py
```



### ⚙️ Configuration (Handling Process Names)

By default, the tool searches for the node name within the process command line or executable name.

If your node name differs significantly from your process name (e.g., a node named `my_algo_node` running inside a generic `python` process), you can manually add a mapping in the `find_pid_by_name` method in `ros_monitor.py`:

```python
def find_pid_by_name(self, node_name):
    # ...
    alias_map = {
        "pointcloud2heightscan_node": "dlio_heightscan_node",
        "mujoco_simulator": "python"
    }
    # ...
```

### 📊 Understanding the Output

| Column | Description |
| --- | --- |
| **Node Name** | Name returned by `ros2 node list`. |
| **Main PID** | The Main Process ID associated with the node. |
| **USR %** | CPU time spent in user mode (Application logic). |
| **SYS %** | CPU time spent in kernel mode (System calls, drivers). **High SYS% (>30%) often indicates excessive data serialization/copying.** |
| **Total %** | Sum of USR and SYS. 100% = 1 Full CPU Core. Includes recursive child processes. |
| **GPU Mem** | VRAM usage associated with the process tree. |
| **GPU Util** | Approximate GPU compute utilization. |

## 🤝 Contribution

Feel free to open issues or PRs if you find any bugs or have suggestions for better PID matching heuristics!