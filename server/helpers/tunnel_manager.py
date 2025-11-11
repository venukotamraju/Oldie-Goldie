import atexit
import re
import subprocess
import sys
import threading
from typing import Optional

class TunnelManager:
    """
    Manage a cloudflared ephemeral tunnel process:
    - start subprocess
    - read stdout in background thread to find trycloudflare URL
    - stop() terminates the process
    """
    URL_REGEX = re.compile(r'https://[-\w]+\.trycloudflare\.com')

    def __init__(self, proc: subprocess.Popen):
        self._proc = proc
        self.url: Optional[str] = None
        self._lock = threading.Lock()
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()
        atexit.register(self.stop)  # safety net
    
    def _read_stdout(self):
        try:
            assert self._proc.stdout is not None
            for raw in self._proc.stdout:
                line = raw.rstrip("\n")
                ## keep logging the cloudflared output
                # print("[cloudflared]", line)
                # Print only the URL
                with self._lock:
                    if self.url is None:
                        m = self.URL_REGEX.search(line)
                        if m:
                            self.url = m.group(0)
                            print(f"🌐 Tunnel active at: {self.url}")
        except Exception as e:
            # reader thread should never crash silently
            print("Error reading cloudflared output:", e, file=sys.stderr)
    
    def stop(self, timeout: float = 5.0):
        """
        Terminate the cloudflared process if still running.
        Safe to call multiple times.
        """
        try:
            if self._proc.poll() is None:
                print("Stopping cloudflared tunnel...")
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    print("cloudflared did not exit, killing...")
                    self._proc.kill()
                    self._proc.wait(timeout=timeout)
        except Exception as e:
            print("Error stopping cloudflared:", e, file=sys.stderr)
    


