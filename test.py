import sys
import time


def _show_percentage(self, _user: str, _percentage, flush: int = 0):
    sys.stdout.write("\b" * flush)
    sys.stdout.write("" * flush)
    sys.stdout.write("\b" * flush)
    msg = 'Load ' + _user + '... ' + str(int(_percentage)) + '%'
    sys.stdout.write(msg)
    return len(msg)


tam = _show_percentage("u", 40.0, 0)
time.sleep(1)
tam = _show_percentage("u", 50.6, 0)
