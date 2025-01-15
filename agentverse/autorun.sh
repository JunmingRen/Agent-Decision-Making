#!/bin/bash

for i in {1..50}; do
  echo "current time: $(date +"%Y-%m-%d %H:%M:%S")"
  agentverse-simulation --task simulation/consistency_check
  echo "Simulation $i completed"
  sleep 1
done
