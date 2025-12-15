#!/bin/bash

PID=`ps -fe | grep 'alan-turing-perfmon.py' | grep -v 'grep' | awk '{print $2}' `
if [ -z "$PID" ]; then
    echo Not running
else
    CMD="kill "$PID
    echo $CMD
    eval $CMD
fi

echo Starting Alan Turing Performance Monitor
nohup /home/alan/AppImage/turing-monitor/bin/python /home/alan/AppImage/turing-monitor/alan-turing-perfmon.py > /dev/null 2>&1 &
disown