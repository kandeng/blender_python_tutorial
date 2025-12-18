#!/usr/bin/bash  #isn't a simple comment 
echo
echo "[INFO] startup.sh is starting up the Blender AI Agent server."

PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONPATH 

mkdir -p logs

echo
echo "[INFO] Stop rabbitmq-server to clean up the environment. Then wait for 5 seconds ..."
sudo systemctl stop rabbitmq-server
sleep 5

echo
echo "[INFO] Start the rabbitmq-server. Then wait for another 5 seconds ..."
sudo systemctl start rabbitmq-server
sleep 5

echo
echo "[INFO] nohup python3 langchain_agent/orchestrator_agent.py > logs/orchestrator_agent_log.txt"
nohup python3 langchain_agent/orchestrator_agent.py > logs/orchestrator_agent_log.txt 2>&1 &

echo
echo "[INFO] nohup python3 fastapi_server/fastapi_engine.py > logs/fastapi_engine_log.txt"
nohup python3 fastapi_server/fastapi_engine.py > logs/fastapi_engine_log.txt 2>&1 &
