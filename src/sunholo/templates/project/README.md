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

curl $VAC_URL/vac/streaming/template \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Can you summarise what the white house executive order will enable in the regulation of LLMs and AI?",
    "chat_history": [{"name": "Human", "content":"Hi! "}, {"name": "AI", "content": "Hi!"}, ]
}'
```