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