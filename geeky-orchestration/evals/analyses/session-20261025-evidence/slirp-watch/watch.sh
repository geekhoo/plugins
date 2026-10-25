#!/bin/bash
# Read-only: snapshot MXC supervisor logs and slirp4netns liveness once a second.
W=$(dirname "$0"); end=$(( $(date +%s) + ${1:-1500} ))
while [ $(date +%s) -lt $end ]; do
  for d in /tmp/mxc-bwrap-proxy-*; do
    [ -d "$d" ] || continue; n=$(basename $d)
    cp -f "$d/supervisor.stderr" "$W/$n.supervisor.stderr" 2>/dev/null
  done
  echo "$(date +%T) slirp=$(pgrep -d, -f '^slirp4netns') bwrap=$(pgrep -c -x bwrap)" >> $W/liveness.log
  sleep 1
done
