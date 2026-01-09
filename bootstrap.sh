#!/usr/bin/env bash
set -e

ACTION="init"

# 参数解析
for arg in "$@"; do
  case $arg in
    --reset)
      ACTION="reset"
      shift
      ;;
    *)
      ;;
  esac
done

echo "=== 智能售药平台脚本执行: $ACTION ==="

# 1. 检查 .env 文件
if [ ! -f infra/.env ]; then
  echo "未检测到 infra/.env，复制示例文件..."
  cp infra/.env.example infra/.env
  echo "请编辑 infra/.env 填入 DEEPSEEK_API_KEY 等配置。"
else
  echo "已检测到 infra/.env。"
fi

if [ "$ACTION" = "reset" ]; then
  echo "执行环境重置..."
  docker compose -f infra/docker-compose.yml down -v
  echo "已清理容器与数据卷。"
fi

# 2. 启动 docker-compose
echo "启动 docker-compose 服务..."
docker compose -f infra/docker-compose.yml up -d

# 3. 初始化 Milvus 集合
echo "初始化 Milvus 集合..."
docker exec -it milvus python /workspace/infra/milvus/init_collection.py || true

# 4. 导入种子数据到 Milvus
echo "导入种子数据到 Milvus..."
docker exec -it pharmacy-api python /app/seeds/seed.py || true

echo "=== 完成: $ACTION ==="
echo "前端访问地址: http://localhost:5173"
echo "后端 API 地址: http://localhost:8000"