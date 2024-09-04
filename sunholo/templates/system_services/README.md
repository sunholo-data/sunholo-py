# Evals

A Cloud Run service that is sent Langfuse IDs, performs evals based on customisable evaluation functions then adds it to the Langfuse database.

## Local

```sh
cd application/system_services/evals 
python app.py
```

```sh
curl http://127.0.0.1:8080

curl http://127.0.0.1:8080/direct_evals \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "9f43dd30-e3d9-4299-9e10-464cae352c7c"
    }'

# only trigger 5% of the time eval_percent=0.05
curl http://127.0.0.1:8080/direct_evals \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "9f43dd30-e3d9-4299-9e10-464cae352c7c",
    "eval_percent": 0.05
    }'
```

## Test calls

```sh
curl https://evals-blqtqfexwa-ew.a.run.app
# {"message":"Hello, evals!"}

curl https://evals-blqtqfexwa-ew.a.run.app/direct_evals \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "9f43dd30-e3d9-4299-9e10-464cae352c7c"
    }'
```