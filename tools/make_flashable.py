#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ make_flashable.py - Backward Compatibility Wrapper ⚡
Routes directly to main.py high-performance engine.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import main

if __name__ == "__main__":
    main()
