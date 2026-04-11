set working-directory := '..'

# Delete all databases and start fresh
reset:
    rm -f data/app.db
    rm -rf data/chroma
    @echo "All databases deleted. They will be recreated on next app start."

# Backfill ChromaDB from SQLite
chroma-backfill *args:
    uv run python scripts/lib/backfill_chroma.py {{args}}

# Open SQLite shell
sqlite *args:
    sqlite3 data/app.db {{args}}

# List all tables in SQLite
tables:
    sqlite3 data/app.db ".tables"

# Show row counts for all tables
counts:
    @sqlite3 data/app.db "SELECT 'conversations', COUNT(*) FROM conversations UNION ALL SELECT 'messages', COUNT(*) FROM messages UNION ALL SELECT 'knowledge_files', COUNT(*) FROM knowledge_files;"

# Show ChromaDB collection stats
chroma-stats:
    uv run python -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma'); [print(f'  {col.name}: {col.count()} items') for col in c.list_collections()]"

# Run RAG pipeline end-to-end integration test
test-rag-e2e:
    uv run python scripts/lib/test_rag_e2e.py
