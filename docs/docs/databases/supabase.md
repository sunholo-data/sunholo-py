# Supabase

[Supabase](https://supabase.com/) is a popular GenAI database that has many great GenAI features build in.

## Usage

To start using Supabase, set your configuration to use it as a memory:

```yaml
    memory:
      - supabase-vectorstore:
          vectorstore: supabase
```

When you create your Supabse account, you will receive these values that need to be added as an environment variable:

- SUPABASE_URL
- SUPABASE_KEY

Supabase also requires a `DB_CONNECTION_STRING` environment variable with the connection string to your deployed Supabase instance.
This will look something like this:

`postgres://postgres.<your-supabase-uri>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`

## Auto-creation of tables

On first embed, if no table is specified the name of the `vector_name`, it will attempt to setup and create a vector store database, using the [SQL within this github folder](https://github.com/sunholo-data/sunholo-py/tree/main/sunholo/database/sql/sb).

