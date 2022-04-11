
import time
import os
from os.path import join, dirname, basename, exists, isfile, isdir

def follow(thefile):
    thefile.seek(0, os.SEEK_END)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

if __name__ == '__main__':
    log_file = join(dirname(dirname(dirname(os.path.realpath(__file__)))),"build","build.log")
    assert exists(log_file)

    logfile = open(log_file)
    loglines = follow(logfile)
    for line in loglines:
        print(line, end='')