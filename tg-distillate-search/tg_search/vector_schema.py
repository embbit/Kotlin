VECTOR_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS message_vectors (
    message_rowid INTEGER PRIMARY KEY REFERENCES messages(rowid) ON DELETE CASCADE,
    embedding BLOB NOT NULL
);
"""
