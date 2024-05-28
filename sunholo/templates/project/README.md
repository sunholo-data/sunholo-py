# Template VAC Project

This is a template VAC project created with `sunholo init my_vac_project`


## Test calls


```shell
export FLASK_URL=https://template-url
curl -X POST ${FLASK_URL}/vac/template \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What do you know about MLOps?"
}'

curl $VAC_URL/vac/streaming/template \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What do you know about MLOps?"
}'
```