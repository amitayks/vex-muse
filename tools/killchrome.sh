#!/usr/bin/env bash
# Kill leftover headless Chrome processes (no ps/pkill on this box). Matches on the executable, not the cmdline.
for p in /proc/[0-9]*; do e=$(readlink "$p/exe" 2>/dev/null); case "$e" in *chrome-headless-shell*) kill -9 "${p#/proc/}" 2>/dev/null;; esac; done; true
