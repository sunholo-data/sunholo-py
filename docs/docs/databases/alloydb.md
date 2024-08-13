# AlloyDB

AlloyDB is a managed PostgreSQL compatible database with AI features such as `pgvector` and the ability to call Vertex AI endpoitns within its SQL.  It also comes with indexes that are high performant over millions of rows.

## Configuration

Below is an example of a `vacConfig` that uses AlloyDB as a vectorstore and docstore

```yaml
...
    docstore:
      - alloydb-docstore:
          type: alloydb
    memory:
      - edmonbrain-vectorstore:
          vectorstore: alloydb
          k: 20
    alloydb_config:
      project_id: multivac-alloydb
      region: europe-west1
      cluster: multivac-alloydb-cluster
      instance: your-instance
```