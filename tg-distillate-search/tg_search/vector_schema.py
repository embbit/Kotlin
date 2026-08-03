"""Schema extension for vector embeddings."""

VECTOR_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS message_vectors (
    message_id INTEGER PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
    embedding BLOB NOT NULL
);
"""
