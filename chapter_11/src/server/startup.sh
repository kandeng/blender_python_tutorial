#!/usr/bin/bash  #isn't a simple comment 
echo
echo "[INFO] startup.sh is starting up the Blender AI Agent server."

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 

mkdir -p logs

nohup python3 langchain/blender_agent_server.py > logs/blender_agent_server_log.txt 2>&1 &
