import psutil
import pandas as pd


class ProcessMonitor:
    @staticmethod
    def get_system_summary(cpu_interval=0.1):
        """Returns high-level system usage metrics safely inside Docker/Linux."""
        if isinstance(cpu_interval, bool) or not isinstance(cpu_interval, (int, float)) or cpu_interval < 0:
            raise ValueError("cpu_interval must be a non-negative number.")
        try:
            memory = psutil.virtual_memory()
            return {
                "cpu_percent": psutil.cpu_percent(interval=cpu_interval),
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids()),
            }
        except (psutil.Error, OSError) as exc:
            raise RuntimeError(f"System metrics could not be read: {exc}") from exc

    @staticmethod
    def get_process_list(top_n=10):
        """Fetches active processes with broad exception handling for containers."""
        if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
            raise ValueError("top_n must be a positive integer.")
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'num_threads', 'create_time']):
                try:
                    info = proc.info
                    info['memory_percent'] = round(info.get('memory_percent') or 0, 2)
                    info['cpu_percent'] = round(info.get('cpu_percent') or 0, 2)
                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError, TypeError):
                    continue
        except (psutil.Error, OSError):
            # Preserve any process rows already collected when enumeration ends early.
            pass
        
        df = pd.DataFrame(processes)
        if not df.empty:
            df = df.sort_values(by="memory_percent", ascending=False).head(top_n)
        else:
            df = pd.DataFrame(columns=['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'num_threads', 'create_time'])
        return df


def get_system_metrics():
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        return cpu, memory
    except Exception:
        return 0.0, 0.0


if __name__ == "__main__":
    mon = ProcessMonitor()
    print("System Summary:", mon.get_system_summary())
    print("\nTop Processes:\n", mon.get_process_list(5))
