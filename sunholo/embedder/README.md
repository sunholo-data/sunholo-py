# Embedder

Turn documents into embedded vectors


## test

Sample:

```
{"page_content": "This is a sample page content. It needs to be at least 100 characters long to pass the test validation.", "metadata": {"vector_name": "sample_vector", "source": "unknown", "eventTime": "2024-04-24T12:00:00Z", "doc_id": "sample_doc_id"}}
```
That encodes as:

```json
{
  "message": {
    "data": "eyJwYWdlX2NvbnRlbnQiOiAiVGhpcyBpcyBhIHNhbXBsZSBwYWdlIGNvbnRlbnQuIEl0IG5lZWRzIHRvIGJlIGF0IGxlYXN0IDEwMCBjaGFyYWN0ZXJzIGxvbmcgdG8gcGFzcyB0aGUgdGVzdCB2YWxpZGF0aW9uLiIsICJtZXRhZGF0YSI6IHsidmVjdG9yX25hbWUiOiAic2FtcGxlX3ZlY3RvciIsICJzb3VyY2UiOiAidW5rbm93biIsICJldmVudFRpbWUiOiAiMjAyNC0wNC0yNFQxMjowMDowMFoiLCAiZG9jX2lkIjogInNhbXBsZV9kb2NfaWQifX0=",
    "messageId": "123456789",
    "publishTime": "2024-04-24T12:00:00Z"
  }
}
```

## curl

```sh
export FLASK_URL=https://embedder-url
curl -X POST ${FLASK_URL}/embed_chunk \
     -H "Content-Type: application/json" \
     -d '{
          "message": {
            "data": "eyJwYWdlX2NvbnRlbnQiOiAiVGhpcyBpcyBhIHNhbXBsZSBwYWdlIGNvbnRlbnQuIEl0IG5lZWRzIHRvIGJlIGF0IGxlYXN0IDEwMCBjaGFyYWN0ZXJzIGxvbmcgdG8gcGFzcyB0aGUgdGVzdCB2YWxpZGF0aW9uLiIsICJtZXRhZGF0YSI6IHsidmVjdG9yX25hbWUiOiAic2FtcGxlX3ZlY3RvciIsICJzb3VyY2UiOiAidW5rbm93biIsICJldmVudFRpbWUiOiAiMjAyNC0wNC0yNFQxMjowMDowMFoiLCAiZG9jX2lkIjogInNhbXBsZV9kb2NfaWQifX0=",
            "messageId": "123456789",
            "publishTime": "2024-04-24T12:00:00Z"
          }
        }'
```