#!/bin/bash

# Check if directories exist
if [ -d "pcap" ]; then
    echo "Cleaning pcap directory..."
    rm -f pcap/*.pcap
else
    echo "pcap directory not found."
fi

if [ -d "csv" ]; then
    echo "Cleaning csv directory..."
    rm -f csv/*.csv
else
    echo "csv directory not found."
fi

if [ -d "logs" ]; then
    echo "Cleaning logs directory..."
    rm -f logs/*.log
else
    echo "logs directory not found."
fi

echo "Cleanup complete."
