# LanceDB

If using LanceDB for your vector store, you can set using the config:

```yaml
kind: vacConfig
apiVersion: v1
vac:
  edmonbrain:
    llm: openai
    agent: edmonbrain
    display_name: Edmonbrain
    avatar_url: https://avatars.githubusercontent.com/u/3155884?s=48&v=4
    description: This is the original [Edmonbrain](https://code.markedmondson.me/running-llms-on-gcp/) implementation that uses RAG to answer questions based on data you send in via its `!help` commands and learns from previous chat history.  It dreams each night that can also be used in its memory.
    model: gpt-4o
    memory:
      - lancedb-vectorstore:
          vectorstore: lancedb
          provider: LanceDB
```
LanceDB will then be used as the vector store destination from both documents added to the bucket and for queries.

To speed up queries, use `create_lancedb_index()` to run periodically and update the index.  An example:

```python
from sunholo.database.lancedb import create_lancedb_index
create_lancedb_index('gs://lancedb-bucket', 'your-vac') 
```

This can be put into a Dockerfile during a build, as `_LANCEDB_BUCKET` is a supported env variable.

```dockerfile
RUN python -c "from sunholo.database.lancedb import create_lancedb_index; create_lancedb_index('${_LANCEDB_BUCKET}', 'edmonbrain')" 
```

## Retrieval

To use within VACs, ensure you have the env var `LANCEDB_BUCKET` set to where the database is stored.  This can be imported during a build via:

```dockerfile
ENV LANCEDB_BUCKET=${_LANCEDB_BUCKET}
```
