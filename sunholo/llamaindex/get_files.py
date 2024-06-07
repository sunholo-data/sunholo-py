try:
    from vertexai.preview import rag
except ImportError:
    rag = None

# Create a RAG Corpus, Import Files
def fetch_corpus(project_id, location, rag_id):
    corpus_name = f"projects/{project_id}/locations/{location}/ragCorpora/{rag_id}"  

    try:
        return rag.get_corpus(name=corpus_name)
    except Exception as err:
        #log.warning(f"Failed to fetch corpus - creating new corpus {str(err)}")
        # it does not create a unique corpus, display_name can be in multiple rag_ids
        #try:
        #    corpus = rag.create_corpus(display_name=vector_name, description=description)
        #except Exception as err:
        #    log.error(f"Failed to get or create corpus {str(err)}")
        raise ValueError(f"Failed to get or create corpus: {str(err)}")