# PostgreSQL databases

When connecting to a PostgreSQL database you can use them for several different GenAI services, such as embeddings, document stores, chat history or analytics.

An alternative to running your own PostgreSQL database is to use the AlloyDB managed service on Google Cloud Platform.

## Embedding

When connecting to a PostgreSQL database for vector embeddings, the `pgvector` extension needs to be installed within the database - refer to the documentation for the specific provider.

When you have the requisite details, then you need a username, password, ip of the PostgreSQL database and the database used to be put into a connection string and set to the `PGVECTOR_CONNECTION_STRING` environment variable - an example is shown below:

```bash
PGVECTOR_CONNECTION_STRING=postgresql://user:password@1.2.3.4:5432/database
```

To use within sunholo, you can use the `pick_retriever()` function to pull in the configuration dynamically according to the `vector_name` argument.

A configuration can be set that will send embeddings after chunking to the database.  

An example config is shown below:

```yaml
kind: vacConfig
apiVersion: v1
vac:
  sample_vector:
    llm: openai
    agent: langserve
    memory:
      - azure_postgres:
          vectorstore: "postgres"
```

This will then return the retriever via 

```python
retriever = pick_retriever("sample_vector")
```

