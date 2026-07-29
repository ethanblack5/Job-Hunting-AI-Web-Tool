import chromadb

chroma_client = chromadb.HttpClient(
    host="13.59.37.174",
    port=8000
)

print(chroma_client.heartbeat())
