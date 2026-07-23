#!/bin/bash
# ALZ Memory Assistant 启动脚本
cd /root/alz-memory-assistant

# 检查 .env
if [ ! -f .env ]; then
  echo "错误：找不到 .env 文件，请先复制 .env.example 并填写 API key"
  exit 1
fi

# 同步记忆库（首次启动必须）
if [ ! -d data/chroma ]; then
  echo "首次启动，初始化记忆库..."
  python3 scripts/sync_memories.py
fi

# 启动服务
echo "启动服务，访问地址：http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000
