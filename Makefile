up:
	docker compose -f infra/docker-compose.yml up -d
milvus-init:
	docker exec -it milvus python /workspace/infra/milvus/init_collection.py
seed:
	docker exec -it pharmacy-api python /app/seeds/seed.py
down:
	docker compose -f infra/docker-compose.yml down