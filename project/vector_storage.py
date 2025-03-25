// ... existing code ...
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
// ... existing code ...

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create custom embeddings class for llama-text-embed-v2
class PineconeEmbeddings:
    def __init__(self, pc_client):
        self.client = pc_client
        self.dimensions = 768  # llama-text-embed-v2 dimension size

    def embed_documents(self, texts):
        embeddings = self.client.inference.embed(
            model="llama-text-embed-v2",
            inputs=texts,
            parameters={"input_type": "passage"}
        )
        return [e['values'] for e in embeddings]

    def embed_query(self, text):
        embedding = self.client.inference.embed(
            model="llama-text-embed-v2",
            inputs=[text],
            parameters={"input_type": "query"}
        )
        return embedding[0]['values']

# Replace OpenAI embeddings with Pinecone embeddings
embeddings = PineconeEmbeddings(pc)

# Initialize Pinecone index
index_name = "smartfile-index"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine"
    )

# Replace Qdrant vectorstore with Pinecone
vectorstore = PineconeVectorStore(
    index=pc.Index(index_name),
    embedding=embeddings,
    text_key="text"
)

// ... existing code ...