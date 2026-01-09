# smart-pharmacy-mcp
目前在经营一个药店，需要开发一个智能售药平台系统，需要满足如下功能：
1. 药品检索工具
   - 从库存系统查询出所有药品名称
   - 根据药品名称通过大模型构建药品基础信息
   - 把药品基础信息存入Milvus向量数据库
2. 规则引擎工具
   - 从药品检索工具中查询出药品
   - 对药品检查禁忌、处方药、红旗标识
   - 返回是否阻止
3.  症状解析工具
   - 输入症状文本
   - 通过症状从药品检索工具中查询出限定范围内的药品
   - 对限定范围药品进行规则引擎过滤，给出药品最小集
   - 把症状及药品最小集输入大模型，给出用药清单
   - 根据用药清单，从库存查询基础信息及价格
   - 用户生成订单数据，根据会员级别给出对应折扣
   - 用户付款
4. 技术选型
   - 开发语言：python/vue3
   - 大模型：Deepseek chat
   - MCP框架：LangChain

## 智能售药平台系统总体方案设计
你要的是一个能落地、可审计、可扩展的系统——既要把药品知识“装进脑子”，又要把风险“拦在门口”。下面给你一套端到端方案，覆盖架构、数据模型、核心流程、MCP/LangChain编排、合规与部署，并给出关键代码骨架（Python/Vue3）。
### 系统架构与模块划分
#### 核心组件
- **前端（Vue3）**：检索、症状输入、规则提示、购物车与结算。
- **API 网关**：统一鉴权、速率限制、审计打点。
- **应用服务（Python/FastAPI）**：
  - **药品检索工具**：库存→基础信息→嵌入→Milvus入库与查询。
  - **规则引擎工具**：禁忌/处方/红旗校验与阻止决策。
  - **症状解析工具**：症状→候选药品→规则过滤→用药清单→订单。
- **向量数据库（Milvus）**：药品向量索引与检索（RAG）。
- **关系型数据库（PostgreSQL/MySQL）**：库存、价格、订单、会员、审计日志。
- **大模型（DeepSeek Chat）**：药品基础信息生成、症状到用药建议、解释说明（OpenAI风格API）。
- **LangChain（MCP 编排）**：工具注册、调用链路、上下文管理、错误回退与审计。
- **身份与合规**：OAuth2/JWT、角色（药师/店员/会员）、处方上传与留存、操作留痕。
#### 逻辑分层
- **Domain 层**：药品、症状、规则、订单等领域对象与服务。
- **Tool 层（MCP）**：检索、规则、症状解析三个工具的统一接口与编排。
- **Infra 层**：Milvus、RDBMS、消息队列（可选，用于异步审计与风控）。
### 数据模型与向量索引
#### 关系型表（示例）
- **drugs**：`id, name, generic_name, spec, manufacturer, is_rx, contraindications_json, flags_json`
- **inventory**：`drug_id, stock, batch_no, expire_date`
- **prices**：`drug_id, list_price, member_tier, discount_rate`
- **orders / order_items**：订单与明细
- **members**：`member_id, tier, points`
- **audit_logs**：`actor, action, entity, before, after, timestamp`
#### Milvus 集合（药品向量）
- **collection**：`drugs_vectors`
- **schema**：
  - `drug_id (INT64, PK)`
  - `name (VARCHAR)`
  - `embedding (FLOAT_VECTOR, dim=1536)`（示例维度，取决于所用 embedding 模型）
  - `metadata (JSON)`：基础信息、禁忌、适应症等
- **索引**：`IVF_FLAT` 或 `HNSW`（视规模与延迟要求）
- **度量**：`COSINE` 或 `L2`
### 三大工具的端到端流程
#### 1) 药品检索工具
- **输入**：无（初始化）/药品名称或语义查询。
- **流程**：
  1. 从库存系统拉取药品清单（批量或增量）。
  2. 调用 DeepSeek 生成药品基础信息（适应症、禁忌、用法用量、是否处方药、红旗标识建议）。
  3. 对基础信息做清洗与结构化（JSON Schema）。
  4. 生成文本拼接（名称+适应症+禁忌+说明）→Embedding→写入 Milvus。
  5. 提供语义检索 API：关键词/症状短语→向量查询→返回候选药品。
- **输出**：候选药品列表（含基础信息与相似度）。
#### 2) 规则引擎工具
- **输入**：药品对象（含基础信息与标识）、用户上下文（年龄、过敏史、妊娠、并用药等）。
- **规则集**（可配置）：
  - **禁忌**：如“妊娠禁用”“肝肾功能不全慎用”等。
  - **处方药**：无处方则阻止；有处方则需药师复核。
  - **红旗标识**：高风险提示（年龄<X、症状持续>Y天、发热>Z℃等）。
- **决策输出**：`allow | block | require_pharmacist_review`，并返回原因与证据路径（审计）。
#### 3) 症状解析工具
- **输入**：症状文本（自然语言）。
- **流程**：
  1. 症状→向量检索（Milvus）限定候选药品集合（Top-K）。
  2. 对候选集合逐一执行规则引擎过滤→得到“药品最小集”（满足安全与适应症）。
  3. 将症状+最小集喂给 DeepSeek，生成**用药清单**（含用法用量、注意事项、何时就医）。
  4. 根据清单查询库存与价格，计算会员折扣，生成订单草案。
  5. 用户确认→支付→落库→审计记录。
- **输出**：可下单的用药清单与解释说明。
### LangChain（MCP）编排设计
#### 工具注册
- **Tool: drug_search**（Milvus 语义检索）
- **Tool: rule_engine**（禁忌/处方/红旗）
- **Tool: symptom_to_plan**（症状→用药建议，调用 DeepSeek）
- **Tool: pricing_inventory**（库存与价格查询）
- **Tool: order_checkout**（订单与折扣计算、支付预处理）
#### 调用链路（简化）
1. `symptom_to_plan`：
   - 调用 `drug_search` 获取 Top-K。
   - 并行调用 `rule_engine` 过滤。
   - 汇总最小集→提示词构造→DeepSeek 生成用药清单。
2. `pricing_inventory`：
   - 对清单逐项查询库存与价格。
3. `order_checkout`：
   - 计算会员折扣→生成订单→返回支付链接或二维码。
#### 审计与可追溯
- 每次工具调用记录：`tool_name, input_hash, output_hash, latency, actor, decision`
- 对模型生成内容保存提示词与响应摘要（合规脱敏）。
### 关键接口与代码骨架（Python/FastAPI + LangChain）
#### 依赖安装（示例）
```bash
pip install fastapi uvicorn langchain pymilvus pydantic requests python-dotenv
```
#### 配置与客户端初始化（DeepSeek & Milvus）
```python
# config.py
import os
from dotenv import load_dotenv
from pymilvus import connections, Collection

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def init_milvus():
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    return Collection("drugs_vectors")  # 需提前创建并建索引
```
（DeepSeek 提供 OpenAI 风格 API，可用 `requests` 或 OpenAI SDK 兼容方式调用。）
#### 药品检索工具（向量入库与查询）
```python
# tools/drug_search.py
from typing import List, Dict
from pymilvus import Collection
import numpy as np

def embed_text(text: str) -> List[float]:
    # 调用 DeepSeek embedding（伪代码）
    # resp = requests.post("https://api.deepseek.com/v1/embeddings", headers=..., json=...)
    # return resp["data"][0]["embedding"]
    return np.random.rand(1536).tolist()  # 占位

def upsert_drug(col: Collection, drug: Dict):
    vec = embed_text(
        f"{drug['name']} {drug['indications']} {drug['contraindications']} {drug['desc']}"
    )
    col.insert([
        [drug["id"]],
        [drug["name"]],
        [vec],
        [drug]  # metadata json
    ])

def search_drugs(col: Collection, query: str, top_k: int = 10) -> List[Dict]:
    qvec = embed_text(query)
    res = col.search([qvec], "embedding", params={"metric_type": "COSINE"}, limit=top_k,
                     output_fields=["drug_id", "name", "metadata"])
    return [{"drug_id": r.id, "name": r.entity.get("name"), "meta": r.entity.get("metadata")}
            for hits in res for r in hits]
```
#### 规则引擎工具（可配置规则）
```python
# tools/rule_engine.py
from typing import Dict

def evaluate_rules(drug: Dict, user_ctx: Dict) -> Dict:
    reasons = []
    decision = "allow"

    # 处方药
    if drug["is_rx"] and not user_ctx.get("prescription_uploaded"):
        decision = "require_pharmacist_review"
        reasons.append("处方药需药师复核或上传处方")

    # 禁忌示例
    contraindications = drug.get("contraindications", [])
    if "pregnancy" in contraindications and user_ctx.get("pregnant"):
        decision = "block"
        reasons.append("妊娠禁用")

    # 红旗示例
    flags = drug.get("flags", [])
    if "fever_high" in flags and user_ctx.get("fever_celsius", 0) >= 39:
        decision = "require_pharmacist_review"
        reasons.append("高热红旗，建议线下就医")

    return {"decision": decision, "reasons": reasons}
```
#### 症状解析工具（编排）
```python
# tools/symptom_to_plan.py
from typing import List, Dict
from .drug_search import search_drugs
from .rule_engine import evaluate_rules

def generate_plan(deepseek_client, symptom_text: str, col, user_ctx: Dict) -> Dict:
    candidates = search_drugs(col, symptom_text, top_k=20)
    minimal_set = []
    for c in candidates:
        r = evaluate_rules(c["meta"], user_ctx)
        if r["decision"] == "allow":
            minimal_set.append({"drug": c, "rule": r})
    # 提示词构造（症状+最小集）
    prompt = {
        "symptom": symptom_text,
        "candidates": [{"name": d["drug"]["name"], "indications": d["drug"]["meta"]["indications"]} for d in minimal_set],
        "constraints": user_ctx
    }
    # 调用 DeepSeek 生成用药清单（伪代码）
    # resp = deepseek_client.chat.completions.create(model="deepseek-chat", messages=[...])
    plan = {"items": [{"drug_id": d["drug"]["drug_id"], "dose": "按说明书", "notes": "多饮水"} for d in minimal_set]}
    return {"plan": plan, "explain": "模型生成的用药建议（需药师复核）"}
```
#### 价格与库存、订单与折扣
```python
# tools/pricing_inventory.py
def enrich_with_price_inventory(db, plan, member_tier: str):
    items = []
    for it in plan["items"]:
        inv = db.get_inventory(it["drug_id"])
        price = db.get_price(it["drug_id"], member_tier)
        items.append({
            **it,
            "stock": inv["stock"],
            "unit_price": price["list_price"],
            "discount_rate": price.get("discount_rate", 1.0),
            "final_price": price["list_price"] * price.get("discount_rate", 1.0)
        })
    return items

# tools/order_checkout.py
def create_order(db, member_id: int, items: list):
    total = sum(i["final_price"] for i in items)
    order_id = db.insert_order(member_id, items, total)
    return {"order_id": order_id, "total": total, "payment_qr": f"/pay/{order_id}"}
```
#### FastAPI 路由（示例）
```python
# app.py
from fastapi import FastAPI, Depends
from config import init_milvus
from tools.symptom_to_plan import generate_plan
from tools.pricing_inventory import enrich_with_price_inventory
from tools.order_checkout import create_order

app = FastAPI()
col = init_milvus()

@app.post("/symptom/plan")
def symptom_plan(payload: dict, user=Depends(...)):
    user_ctx = payload.get("user_ctx", {})
    plan = generate_plan(deepseek_client=None, symptom_text=payload["symptom"], col=col, user_ctx=user_ctx)
    items = enrich_with_price_inventory(db=..., plan=plan["plan"], member_tier=user["tier"])
    order = create_order(db=..., member_id=user["id"], items=items)
    return {"plan": plan, "items": items, "order": order}
```
### 前端（Vue3）页面与交互
#### 页面
- **药品检索**：关键词/症状输入→候选列表→规则提示徽章（禁忌/处方/红旗）。
- **症状解析**：输入症状→生成用药清单→库存与价格→加入购物车。
- **结算**：会员折扣展示→支付二维码→订单状态轮询。
- **审计与复核**（药师端）：查看模型建议、规则决策、允许/阻止/修改。
#### 组件要点
- **Badge 提示**：`禁忌/处方/红旗` 三色标识。
- **Explain 面板**：展示模型生成的理由与规则命中点。
- **合规弹窗**：处方药下单前必须上传处方或药师复核。
### 合规、安全与审计
- **角色与权限**：会员、店员、药师、管理员分级授权。
- **处方管理**：上传、OCR（可选）、药师复核记录、留存期与访问审计。
- **数据最小化**：仅保留必要的用户健康信息，敏感字段加密存储。
- **可解释性**：模型输出附带提示词摘要与规则命中点；所有自动决策可人工覆盖。
- **风控**：高风险症状（红旗）强制建议线下就医；频繁购买特定药品触发人工复核。
- **日志与追溯**：工具调用、模型响应、规则决策、订单变更全量打点。
### 部署与运维
- **容器化**：前后端、Milvus、DB 分别容器化；Kubernetes/Helm 管理。
- **环境**：`dev/staging/prod` 分层；API Key 与密钥用 Vault/Secrets 管理。
- **监控**：请求延迟、Milvus QPS/召回率、模型调用成功率、规则阻止率、订单转化率。
- **成本控制**：Embedding 与 Chat 分账；缓存热门药品向量与说明；批量入库离线化。
### 技术选型落地建议
- **开发语言**：后端 Python（FastAPI），前端 Vue3（Vite）。
- **大模型**：DeepSeek Chat（OpenAI风格 API，便于与 LangChain 集成）。
- **MCP 框架**：LangChain 工具化编排、回退策略与审计中间件。
- **向量库**：Milvus（成熟的向量检索，适合医疗/零售场景的 RAG）。
- **数据库**：PostgreSQL/MySQL；必要时加 Redis 做会话与缓存。
### 风险与边界
- **模型幻觉**：所有用药建议必须标注“需药师复核”，关键药品信息以权威数据源为准。
- **规则覆盖**：禁忌与红旗需持续维护；引入外部药典数据源时要做版本化与来源标注。
- **处方合规**：不同地区法规差异，处方上传与审核流程需本地化。
- **召回质量**：Milvus检索效果依赖嵌入模型与文本清洗；定期评估 Top-K 命中率与用户反馈。
### 你可以先做的两周冲刺里程碑
1. **Week 1**
   - 建表与 Milvus 集合创建；库存导入与 50 种常见药品基础信息生成与入库。
   - 完成 `drug_search` 与 `rule_engine` 的 API。
   - Vue3 原型页：检索与规则徽章展示。
2. **Week 2**
   - 完成 `symptom_to_plan` 编排与订单链路（价格/库存/折扣）。
   - 加入审计日志与药师复核页。
   - 压测与灰度上线，收集用户反馈与规则命中数据。
    
## 最小可用仓库结构（Python/FastAPI + Vue3 + Milvus + LangChain + DeepSeek）
下面是一套可直接运行的最小可用骨架，包含后端、前端、向量库、关系库与容器编排。你可以一键 `docker compose up -d` 拉起全栈，然后用种子数据完成药品入库、向量化与检索。DeepSeek 使用 OpenAI 风格 API，Milvus 作为向量检索引擎，LangChain 负责工具编排与审计。参考 Milvus 官方的 DeepSeek RAG 教程可快速对齐依赖与调用方式。 
### 仓库目录结构
```text
smart-pharmacy/
├─ backend/
│  ├─ app.py
│  ├─ config.py
│  ├─ domain/
│  │  ├─ models.py
│  │  └─ schemas.py
│  ├─ tools/
│  │  ├─ drug_search.py
│  │  ├─ rule_engine.py
│  │  ├─ symptom_to_plan.py
│  │  ├─ pricing_inventory.py
│  │  └─ order_checkout.py
│  ├─ mcp/
│  │  ├─ registry.py
│  │  └─ audit.py
│  ├─ seeds/
│  │  ├─ drugs.csv
│  │  └─ seed.py
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  ├─ src/
│  │  ├─ main.ts
│  │  ├─ App.vue
│  │  ├─ pages/
│  │  │  ├─ Search.vue
│  │  │  ├─ Symptom.vue
│  │  │  └─ Checkout.vue
│  │  └─ components/
│  │     ├─ DrugCard.vue
│  │     ├─ RuleBadge.vue
│  │     └─ ExplainPanel.vue
│  ├─ index.html
│  ├─ package.json
│  └─ Dockerfile
├─ infra/
│  ├─ docker-compose.yml
│  ├─ milvus/
│  │  ├─ init_collection.py
│  │  └─ README.md
│  ├─ db/
│  │  ├─ init.sql
│  │  └─ README.md
│  └─ .env.example
├─ Makefile
└─ README.md
```
### 环境与容器编排
#### docker-compose.yml（Milvus + Postgres + Backend + Frontend）
```yaml
version: "3.9"
services:
  milvus:
    image: milvusdb/milvus:2.4.6
    container_name: milvus
    ports: ["19530:19530", "9091:9091"]
    environment:
      - MILVUS_LOG_LEVEL=info
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "19530"]
      interval: 10s
      timeout: 5s
      retries: 10

  postgres:
    image: postgres:16
    container_name: pharmacy-db
    environment:
      - POSTGRES_PASSWORD=pharmacy
      - POSTGRES_USER=pharmacy
      - POSTGRES_DB=pharmacy
    ports: ["5432:5432"]
    volumes:
      - ./infra/db/init.sql:/docker-entrypoint-initdb.d/init.sql

  backend:
    build: ./backend
    container_name: pharmacy-api
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
      - DB_URL=postgresql://pharmacy:pharmacy@pharmacy-db:5432/pharmacy
    depends_on: [milvus, postgres]
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    container_name: pharmacy-web
    depends_on: [backend]
    ports: ["5173:5173"]
```
#### 后端 Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
#### 前端 Dockerfile
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```
#### .env.example
```env
DEEPSEEK_API_KEY=your_deepseek_key
MILVUS_HOST=localhost
MILVUS_PORT=19530
DB_URL=postgresql://pharmacy:pharmacy@localhost:5432/pharmacy
```
### 后端实现（关键文件）
#### requirements.txt
```text
fastapi
uvicorn
langchain
pymilvus
psycopg2-binary
pydantic
python-dotenv
requests
```
#### config.py
```python
import os
from dotenv import load_dotenv
from pymilvus import connections, Collection

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DB_URL = os.getenv("DB_URL")
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def init_milvus():
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    return Collection("drugs_vectors")  # 需先创建
```
#### infra/milvus/init_collection.py
```python
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection

connections.connect(host="milvus", port="19530")

fields = [
    FieldSchema(name="drug_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=256),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
    FieldSchema(name="metadata", dtype=DataType.JSON),
]
schema = CollectionSchema(fields, description="Drug vectors")
col = Collection("drugs_vectors", schema)
col.create_index(field_name="embedding", index_params={"index_type":"HNSW","metric_type":"COSINE","params":{"M":16,"efConstruction":200}})
print("Milvus collection ready.")
```
#### infra/db/init.sql
```sql
CREATE TABLE IF NOT EXISTS drugs (
  id BIGINT PRIMARY KEY,
  name TEXT NOT NULL,
  generic_name TEXT,
  spec TEXT,
  manufacturer TEXT,
  is_rx BOOLEAN DEFAULT FALSE,
  contraindications_json JSONB,
  flags_json JSONB
);

CREATE TABLE IF NOT EXISTS inventory (
  drug_id BIGINT REFERENCES drugs(id),
  stock INT DEFAULT 0,
  batch_no TEXT,
  expire_date DATE
);

CREATE TABLE IF NOT EXISTS prices (
  drug_id BIGINT REFERENCES drugs(id),
  list_price NUMERIC(10,2),
  member_tier TEXT,
  discount_rate NUMERIC(5,2) DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS orders (
  id BIGSERIAL PRIMARY KEY,
  member_id BIGINT,
  total NUMERIC(10,2),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
  order_id BIGINT REFERENCES orders(id),
  drug_id BIGINT,
  qty INT,
  unit_price NUMERIC(10,2),
  final_price NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor TEXT,
  action TEXT,
  entity TEXT,
  before JSONB,
  after JSONB,
  ts TIMESTAMP DEFAULT NOW()
);
```
#### backend/domain/schemas.py（Pydantic）
```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class UserCtx(BaseModel):
    age: Optional[int] = None
    pregnant: Optional[bool] = None
    prescription_uploaded: Optional[bool] = None
    fever_celsius: Optional[float] = None

class SymptomRequest(BaseModel):
    symptom: str
    user_ctx: UserCtx

class PlanItem(BaseModel):
    drug_id: int
    dose: str
    notes: str

class Plan(BaseModel):
    items: List[PlanItem]
```
#### backend/tools/drug_search.py
```python
from typing import List, Dict
from pymilvus import Collection
import numpy as np

def embed_text(text: str) -> List[float]:
    # 这里可替换为 DeepSeek Embedding（OpenAI风格 API）
    # 参考 Milvus 文档中的 DeepSeek 集成说明。 
    return np.random.rand(1536).tolist()

def upsert_drug(col: Collection, drug: Dict):
    vec = embed_text(
        f"{drug['name']} {drug.get('indications','')} {drug.get('contraindications','')} {drug.get('desc','')}"
    )
    col.insert([[drug["id"]], [drug["name"]], [vec], [drug]])

def search_drugs(col: Collection, query: str, top_k: int = 10) -> List[Dict]:
    qvec = embed_text(query)
    res = col.search([qvec], "embedding", params={"metric_type":"COSINE"}, limit=top_k,
                     output_fields=["drug_id","name","metadata"])
    out = []
    for hits in res:
        for r in hits:
            out.append({
                "drug_id": r.id,
                "name": r.entity.get("name"),
                "meta": r.entity.get("metadata")
            })
    return out
```
#### backend/tools/rule_engine.py
```python
from typing import Dict

def evaluate_rules(drug: Dict, user_ctx: Dict) -> Dict:
    reasons, decision = [], "allow"

    if drug.get("is_rx") and not user_ctx.get("prescription_uploaded"):
        decision = "require_pharmacist_review"
        reasons.append("处方药需药师复核或上传处方")

    contraindications = drug.get("contraindications", [])
    if "pregnancy" in contraindications and user_ctx.get("pregnant"):
        decision = "block"
        reasons.append("妊娠禁用")

    flags = drug.get("flags", [])
    if "fever_high" in flags and (user_ctx.get("fever_celsius") or 0) >= 39:
        decision = "require_pharmacist_review"
        reasons.append("高热红旗，建议线下就医")

    return {"decision": decision, "reasons": reasons}
```
#### backend/tools/symptom_to_plan.py
```python
from typing import Dict
from .drug_search import search_drugs
from .rule_engine import evaluate_rules

def generate_plan(symptom_text: str, col, user_ctx: Dict) -> Dict:
    candidates = search_drugs(col, symptom_text, top_k=20)
    minimal = []
    for c in candidates:
        r = evaluate_rules(c["meta"], user_ctx)
        if r["decision"] == "allow":
            minimal.append({"drug": c, "rule": r})

    plan = {"items": [{"drug_id": d["drug"]["drug_id"], "dose": "按说明书", "notes": "多饮水"} for d in minimal]}
    return {"plan": plan, "explain": "模型建议需药师复核"}
```
#### backend/tools/pricing_inventory.py 与 order_checkout.py
```python
def enrich_with_price_inventory(db, plan, member_tier: str):
    items = []
    for it in plan["items"]:
        inv = db.get_inventory(it["drug_id"])
        price = db.get_price(it["drug_id"], member_tier)
        items.append({
            **it,
            "stock": inv["stock"],
            "unit_price": price["list_price"],
            "discount_rate": price.get("discount_rate", 1.0),
            "final_price": price["list_price"] * price.get("discount_rate", 1.0)
        })
    return items

def create_order(db, member_id: int, items: list):
    total = sum(i["final_price"] for i in items)
    order_id = db.insert_order(member_id, items, total)
    return {"order_id": order_id, "total": total, "payment_qr": f"/pay/{order_id}"}
```
#### backend/mcp/registry.py（工具注册与审计）
```python
from typing import Callable, Dict
from .audit import audit_log

TOOLS: Dict[str, Callable] = {}

def register_tool(name: str, fn: Callable):
    TOOLS[name] = fn

def call_tool(name: str, *args, **kwargs):
    res = TOOLS[name](*args, **kwargs)
    audit_log(name, args, kwargs, res)
    return res
```
#### backend/mcp/audit.py
```python
import json, time

def audit_log(tool, args, kwargs, res):
    print(json.dumps({
        "ts": time.time(),
        "tool": tool,
        "args": str(args),
        "kwargs": kwargs,
        "result_summary": str(res)[:200]
    }))
```
#### backend/app.py（FastAPI 路由）
```python
from fastapi import FastAPI
from config import init_milvus
from tools.symptom_to_plan import generate_plan
from tools.pricing_inventory import enrich_with_price_inventory
from tools.order_checkout import create_order

app = FastAPI()
col = init_milvus()

# 伪 DB 适配器（示例）
class DB:
    def get_inventory(self, drug_id): return {"stock": 100}
    def get_price(self, drug_id, tier): return {"list_price": 39.9, "discount_rate": 0.9 if tier=="gold" else 1.0}
    def insert_order(self, member_id, items, total): return 10001

db = DB()

@app.post("/symptom/plan")
def symptom_plan(payload: dict):
    user_ctx = payload.get("user_ctx", {})
    plan = generate_plan(symptom_text=payload["symptom"], col=col, user_ctx=user_ctx)
    items = enrich_with_price_inventory(db=db, plan=plan["plan"], member_tier=payload.get("member_tier","basic"))
    order = create_order(db=db, member_id=payload.get("member_id",1), items=items)
    return {"plan": plan, "items": items, "order": order}
```
#### backend/seeds/seed.py（种子数据入库）
```python
import csv, json
from pymilvus import connections, Collection
from tools.drug_search import upsert_drug

connections.connect(host="milvus", port="19530")
col = Collection("drugs_vectors")

with open("seeds/drugs.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        drug = {
            "id": int(row["id"]),
            "name": row["name"],
            "indications": row.get("indications",""),
            "contraindications": json.loads(row.get("contraindications","[]")),
            "flags": json.loads(row.get("flags","[]")),
            "is_rx": row.get("is_rx","false").lower()=="true",
            "desc": row.get("desc","")
        }
        upsert_drug(col, drug)
print("Seeded drugs into Milvus.")
```
### 前端（Vue3）最小页面
#### package.json
```json
{
  "name": "pharmacy-web",
  "scripts": { "dev": "vite" },
  "dependencies": { "vue": "^3.4.0", "axios": "^1.6.0" },
  "devDependencies": { "vite": "^5.0.0", "@vitejs/plugin-vue": "^5.0.0" }
}
``
#### src/main.ts
```ts
import { createApp } from "vue";
import App from "./App.vue";
createApp(App).mount("#app");
```
#### src/App.vue（路由简化为单页）
```vue
<template>
  <div class="p-4">
    <h2>症状解析与下单</h2>
    <textarea v-model="symptom" rows="4" placeholder="输入症状..."></textarea>
    <button @click="submit">生成用药清单</button>

    <div v-if="resp">
      <h3>用药清单</h3>
      <pre>{{ resp.plan }}</pre>
      <h3>价格与库存</h3>
      <pre>{{ resp.items }}</pre>
      <h3>订单</h3>
      <pre>{{ resp.order }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { ref } from "vue";
const symptom = ref("");
const resp = ref<any>(null);
async function submit() {
  const { data } = await axios.post("http://localhost:8000/symptom/plan", {
    symptom: symptom.value,
    user_ctx: { pregnant: false, prescription_uploaded: false, fever_celsius: 37.5 },
    member_tier: "gold",
    member_id: 1
  });
  resp.value = data;
}
</script>
```
### 一键启动与初始化
#### Makefile
```makefile
up:
\tdocker compose -f infra/docker-compose.yml up -d
milvus-init:
\tdocker exec -it milvus python /workspace/infra/milvus/init_collection.py
seed:
\tdocker exec -it pharmacy-api python /app/seeds/seed.py
down:
\tdocker compose -f infra/docker-compose.yml down
```
#### 启动步骤
1. **配置密钥**：复制 `infra/.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY`。
2. **启动容器**：`make up`
3. **初始化 Milvus 集合**：`make milvus-init`
4. **导入种子数据**：`make seed`
5. **访问前端**：浏览器打开 `http://localhost:5173`，输入症状并生成用药清单。

> 说明：DeepSeek 的 Embedding/Chat 在本骨架中以占位实现；你可以按 Milvus 官方教程替换为真实调用（OpenAI风格 API），并将生成的药品基础信息与嵌入写入 Milvus。 
### 后续增强建议
- **真实 DeepSeek 接入**：将 `embed_text` 与症状到用药建议改为真实 API；为提示词与响应做审计留痕。
- **规则配置中心**：把禁忌/红旗/处方规则抽成 JSON Schema 与管理后台。
- **药师复核页**：在前端增加复核工作流与覆盖决策能力。
- **召回评估**：定期评估 Milvus Top-K 命中率与用户反馈，优化文本清洗与索引参数。
- **云上托管**：如需云上托管与一体化工作流，可参考云厂商的 Milvus+LangChain+DeepSeek RAG 方案文章进行扩展。 

## 功能列表
- 症状解析工具：输入症状文本 → 输出结构化症状、红旗标记。
- 药品检索工具：限定药店自有药品，通过 API 查询。
- 规则引擎工具：检查禁忌、处方药、红旗 → 返回是否阻止。
- 订单服务工具：生成订单，自动计算会员折扣。
- 复核日志工具：记录药师操作（批准/驳回及原因）。
- 统计报表工具：按药师和时间范围统计批准/驳回数量。
## 药品系统信息
### 🏷️ 基本信息
- **药品通用名**：国际通用或国家标准名称。  
- **商品名/品牌名**：市场销售名称。  
- **剂型**：片剂、胶囊、注射液、口服液等。  
- **规格**：每片/每支含量，如 500mg/片。  
- **包装信息**：包装单位、数量。  
### 📚 药理与适应症
- **药理作用**：主要机制，如抗菌、解热镇痛。  
- **适应症**：常见的治疗用途（例如：用于缓解咳嗽、退烧）。  
- **禁忌症**：不适合使用的情况（如孕妇、儿童、肝肾功能不全）。  
- **注意事项**：特殊人群使用注意。  
### ⚠️ 安全与合规信息
- **不良反应**：可能出现的副作用。  
- **相互作用**：与其他药物、食物的相互影响。  
- **警示信息**：黑框警告或监管要求。  
- **批准文号**：国家药监局或 FDA 批准编号。  
### 🏥 管理与流通信息
- **生产厂家**：药品生产企业。  
- **流通渠道**：批发、零售、医院药房。  
- **库存与有效期**：药品批次、保质期、库存数量。  
- **监管分类**：处方药、非处方药（OTC）、特殊管理药品。  
### 📊 扩展信息
- **价格信息**：零售价、医保报销价格。  
- **医保目录情况**：是否纳入医保。  
- **临床指南推荐**：是否在临床路径或指南中推荐。  
- **电子化编码**：如药品编码、条形码、UDI。
### 📌 总结
👉 药品系统信息通常包括 **基本信息、药理与适应症、安全与合规、管理与流通、扩展信息** 五大类。这些信息共同保证药品在研发、生产、流通、临床使用和监管环节的透明与合规。  
