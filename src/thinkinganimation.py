from itertools import cycle
from sys import stdout
from threading import Thread
from time import sleep
from typing import List


class ThinkingAnimation:
    def __init__(self, symbols: List[str] | None = None):
        self.thinking = False
        self.spinner = cycle(symbols if symbols is not None else ['⣷','⣯','⣟','⡿','⢿','⣻','⣽','⣾'])
        self.thread = None
        self.interval = 0.1

    def start(self, interval: float | None = None):
        if not self.thinking:
            self.thinking = True
            if interval is not None:
                self.interval = interval
            # Move to new line for spinner
            stdout.write('\n')
            stdout.flush()
            self.thread = Thread(target=self._animate, daemon=True)
            self.thread.start()

    def stop(self):
        if self.thinking:
            self.thinking = False
            if self.thread is not None:
                self.thread.join()
                self.thread = None
                # Clear spinner line and move cursor back up
                stdout.write('\r\033[K')  # Clear current line
                stdout.write('\033[1A')   # Move cursor up one line
                stdout.flush()

    def _animate(self):
        while self.thinking:
            for symbol in self.spinner:
                if not self.thinking:
                    break
                stdout.write(f'\r{symbol} ')
                stdout.flush()
                sleep(self.interval)

if __name__ == "__main__":
    animation = ThinkingAnimation(['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'])
    animation.start(0.1)
    sleep(5)
    animation.stop()
    exit(0)