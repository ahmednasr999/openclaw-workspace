#!/usr/bin/env python3
import os
config_dir = "/root/.openclaw/workspace/config"
for f in os.listdir(config_dir):
    print(f)
