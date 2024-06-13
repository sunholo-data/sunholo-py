# Senses

Helping models see and hear

## Livekit

https://docs.livekit.io/home/cli/cli-setup/

```sh
brew install livekit livekit-cli
```

Start local server:

```sh
livekit-server --dev --bind 0.0.0.0
```

Note URL: wss://127.0.0.1:7881

Create token:

```sh
livekit-cli create-token \
    --api-key devkey --api-secret secret \
    --join --room my-first-room --identity user1 \
    --valid-for 24h
```