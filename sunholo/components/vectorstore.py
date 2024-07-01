#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import os
from ..logging import log

def pick_vectorstore(vs_str: str, vector_name: str, embeddings, read_only=None):
    log.debug('Picking vectorstore')
        
    if vs_str == 'supabase':
        from supabase import Client, create_client
        from langchain_community.vectorstores import SupabaseVectorStore

        from ..database.database import setup_supabase

        if not read_only:
            log.debug(f"Initiating Supabase store: {vector_name}")
            setup_supabase(vector_name)

        # init embedding and vector store
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        log.debug(f"Supabase URL: {supabase_url} vector_name: {vector_name}")

        supabase: Client = create_client(supabase_url, supabase_key)

        vectorstore = SupabaseVectorStore(supabase, 
                                        embeddings,
                                        table_name=vector_name,
                                        query_name=f'match_documents_{vector_name}')

        log.debug("Chose Supabase")

        return vectorstore
    
    elif vs_str == 'cloudsql' or vs_str == 'postgres':
        from langchain_community.vectorstores import PGVector

        log.debug("Inititaing CloudSQL/Postgres pgvector")
        #setup_cloudsql(vector_name) 

        # https://python.langchain.com/docs/modules/data_connection/vectorstores/integrations/pgvector
        CONNECTION_STRING = os.environ.get("PGVECTOR_CONNECTION_STRING")
        # postgresql://brainuser:password@10.24.0.3:5432/brain

        from ..database.database import get_vector_size
        vector_size = get_vector_size(vector_name)

        os.environ["PGVECTOR_VECTOR_SIZE"] = str(vector_size)
        vectorstore = PGVector(connection_string=CONNECTION_STRING,
            embedding_function=embeddings,
            collection_name=vector_name,
            #pre_delete_collection=True # for testing purposes
            )

        log.debug("Chose CloudSQL")

        return vectorstore
    
    elif vs_str == 'alloydb':
        from langchain_google_alloydb_pg import AlloyDBVectorStore
        from ..database.alloydb import create_alloydb_table, create_alloydb_engine
        from ..database.database import get_vector_size

        vector_size = get_vector_size(vector_name)
        engine = create_alloydb_engine(vector_name)

        table_name = f"{vector_name}_vectorstore_{vector_size}"
        if not read_only:
            table_name = create_alloydb_table(vector_name, engine)

        log.info(f"Chose AlloyDB with table name {table_name}")
        vectorstore = AlloyDBVectorStore.create_sync(
                engine=engine,
                table_name=table_name,
                embedding_service=embeddings,
                metadata_columns=["source", "docstore_doc_id"]
                #metadata_columns=["source", "eventTime"]
            )
        return vectorstore
        
    elif vs_str == "lancedb":
        from ..patches.langchain.lancedb import LanceDB
        import lancedb

        LANCEDB_BUCKET = os.environ.get("LANCEDB_BUCKET")
        if LANCEDB_BUCKET is None:
            log.error(f"Could not locate LANCEDB_BUCKET environment variable for {vector_name}")
        log.info(f"LANCEDB_BUCKET environment variable found for {vector_name} - {LANCEDB_BUCKET}")

        try:
            log.info(f"Attempting LanceDB connection to {vector_name} for {LANCEDB_BUCKET}")
            db = lancedb.connect(LANCEDB_BUCKET)
        except Exception as err:
            log.error(f"Could not connect to {LANCEDB_BUCKET} - {str(err)}")

        log.info(f"LanceDB Tables: {db.table_names()} using {LANCEDB_BUCKET}")
        log.info(f"Opening LanceDB table: {vector_name} using {LANCEDB_BUCKET}")
    
        try:
            table = db.open_table(vector_name)
        except FileNotFoundError as err:
            if not read_only:
                log.info(f"{err} - Could not open table for {vector_name} - creating new table")
                init = f"Creating new table for {vector_name}"
                table = db.create_table(
                            vector_name,
                            data=[
                                {
                                    "vector": embeddings.embed_query(init),
                                    "text": init,
                                    "id": "1",
                                }
                            ],
                            mode="overwrite",
                        )
            else:
                log.info(f"{err} - Could not create table for {vector_name} as read_only=True")

        log.info(f"Initiating LanceDB object for {vector_name} using {LANCEDB_BUCKET}")
        vectorstore = LanceDB(
            connection=table,
            embedding=embeddings,
        )
        log.info(f"Chose LanceDB for {vector_name} using {LANCEDB_BUCKET}")

        return vectorstore
 
