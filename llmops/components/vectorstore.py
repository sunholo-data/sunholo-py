#   Copyright [2023] [Sunholo ApS]
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
import logging

from ..utils import load_config_key

def pick_vectorstore(vs_str, vector_name, embeddings):
    logging.debug('Picking vectorstore')
        
    if vs_str == 'supabase':
        from supabase import Client, create_client
        from langchain.vectorstores import SupabaseVectorStore
        from ..database.database import setup_supabase

        logging.debug(f"Initiating Supabase store: {vector_name}")
        setup_supabase(vector_name)

        # init embedding and vector store
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        logging.debug(f"Supabase URL: {supabase_url} vector_name: {vector_name}")

        supabase: Client = create_client(supabase_url, supabase_key)

        vectorstore = SupabaseVectorStore(supabase, 
                                        embeddings,
                                        table_name=vector_name,
                                        query_name=f'match_documents_{vector_name}')

        logging.debug("Chose Supabase")
    elif vs_str == 'cloudsql':
        from langchain.vectorstores.pgvector import PGVector

        logging.debug("Inititaing CloudSQL pgvector")
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

        logging.debug("Chose CloudSQL")
    elif vs_str == 'alloydb':  # exact same as CloudSQL for now
        from langchain.vectorstores.pgvector import PGVector

        logging.info("Inititaing AlloyDB pgvector")
        #setup_cloudsql(vector_name) 

        # https://python.langchain.com/docs/modules/data_connection/vectorstores/integrations/pgvector
        CONNECTION_STRING = os.environ.get("ALLOYDB_CONNECTION_STRING",None)
        if CONNECTION_STRING is None:
            logging.info("Did not find ALLOYDB_CONNECTION_STRING fallback to PGVECTOR_CONNECTION_STRING")
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

        logging.info("Chose AlloyDB")

    else:
        raise NotImplementedError(f'No llm implemented for {vs_str}')   

    return vectorstore