# Chunker service

Turns docs,urls and gs:// urls into document chunks.


# Chunks

```json
# encoded
# eyJwYWdlX2NvbnRlbnQiOiJUZXN0IGNvbnRlbnQiLCAibWV0YWRhdGEiOnsic291cmNlIjoidGVzdF9zb3VyY2UifX0=
{"page_content":"Test content", "metadata":{"source":"test_source"}}
```

If not return_chunks=True, will send it on to the PubSub async service 
TODO: implement other message queues

```bash 
export FLASK_URL=https://chunker-url
curl -X POST ${FLASK_URL}/pubsub_to_store \
     -H "Content-Type: application/json" \
     -d '{
          "message": {
            "data": "eyJwYWdlX2NvbnRlbnQiOiJUZXN0IGNvbnRlbnQiLCAibWV0YWRhdGEiOnsic291cmNlIjoidGVzdF9zb3VyY2UifX0=",
            "attributes": {
              "namespace": "sample_vector",
              "return_chunks": true
            }
          }
        }'
```
