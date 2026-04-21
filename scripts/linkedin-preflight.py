#!/usr/bin/env python3
import os
import subprocess
import sys

TARGET = '/root/.openclaw/workspace-cmo/scripts/linkedin-preflight.py'


def main():
    cmd = [sys.executable, TARGET, *sys.argv[1:]]
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
