""" from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool
import vertexai
 """
""" # Enhance generation
# Create a RAG retrieval tool
rag_retrieval_tool = Tool.from_retrieval(
    retrieval=rag.Retrieval(
        source=rag.VertexRagStore(
            rag_corpora=[rag_corpus.name],  # Currently only 1 corpus is allowed.
            similarity_top_k=3,  # Optional
        ),
    )
)
# Create a gemini-pro model instance
rag_model = GenerativeModel(
    model_name="gemini-1.0-pro-002", tools=[rag_retrieval_tool]
)

# Generate response
response = rag_model.generate_content("What is RAG and why it is helpful?")
print(response.text) """