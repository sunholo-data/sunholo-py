import os
try:
    import pg8000
    import sqlalchemy
    from sqlalchemy.exc import DatabaseError, ProgrammingError
    from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBVectorStore
except ImportError:
    AlloyDBEngine = None
    pass

from .database import get_vector_size
from .uuid import generate_uuid_from_object_id
from ..custom_logging import log
from ..utils import ConfigManager
from ..components import get_embeddings

class AlloyDBClient:
    """
    A class to manage interactions with an AlloyDB instance.

    Example Usage:

    ```python
    client = AlloyDBClient(
        project_id="your-project-id",
        region="your-region",
        cluster_name="your-cluster-name",
        instance_name="your-instance-name",
        user="your-db-user",
        password="your-db-password"
    )

    # Create a database
    client.execute_sql("CREATE DATABASE my_database")

    # Execute other SQL statements
    client.execute_sql("CREATE TABLE my_table (id INT, name VARCHAR(50))")
    ```
    """

    def __init__(self, 
                 config:ConfigManager,
                 project_id: str=None, 
                 region: str=None, 
                 cluster_name:str=None, 
                 instance_name:str=None, 
                 user:str=None,
                 password:str=None,
                 db="postgres"):
        """Initializes the AlloyDB client.
         - project_id (str): GCP project ID where the AlloyDB instance resides.
         - region (str): The region where the AlloyDB instance is located.
         - cluster_name (str): The name of the AlloyDB cluster.
         - instance_name (str): The name of the AlloyDB instance.
         - user (str): If user is None will use the default service email
         - db_name (str): The name of the database.
        """
        if config is None:
            if project_id is None or region is None or cluster_name is None or instance_name is None:
                raise ValueError("Must specify config or project_id, region, cluster_name, instance_name")
        if config:
            alloydb_config = config.vacConfig("alloydb_config")
            if not alloydb_config:
                raise ValueError("Must specify vac.alloydb_config")
            self.config = alloydb_config
            self.vector_name = self.config.get("vac")
            project_id = alloydb_config["project_id"]
            region = alloydb_config["region"]
            cluster_name = alloydb_config["cluster"]
            instance_name = alloydb_config["instance"]

        ALLOYDB_DB = os.environ.get("ALLOYDB_DB")
        if ALLOYDB_DB is None and alloydb_config.get("database") is None:
            log.warning("Could not locate ALLOYDB_DB environment variable or 'alloydb_config.database'")
        
        self.database = alloydb_config.get("database") or ALLOYDB_DB or db
        if not self.database:
            raise ValueError("Could not derive a database to query")

        self.user = user
        self.password = password
        self.inst_url = ""
        if user:
            log.info("User specified {user} - using pg8000 engine")
            self.inst_url = self._build_instance_uri(project_id, region, cluster_name, instance_name)
            self.engine = self._create_engine_from_pg8000()
            self.engine_type = "pg8000"
        else:
            log.info("Build with Langchain engine - will use default service account for auth")
            self.engine = self._create_engine()
            self.engine_type = "langchain"
               
        self.vectorstore = None

    def _build_instance_uri(self, project_id, region, cluster_name, instance_name):
        return f"projects/{project_id}/locations/{region}/clusters/{cluster_name}/instances/{instance_name}"
    
    def _create_engine_from_pg8000(self, user, password, db):
        def getconn() -> pg8000.dbapi.Connection:
            conn = self.connector.connect(
                self.inst_uri,
                "pg8000",
                user=user,
                password=password,
                db=db,
                enable_iam_auth=True,
            )
            return conn

        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://", 
            isolation_level="AUTOCOMMIT", 
            creator=getconn)
        engine.dialect.description_encoding = None

        log.info(f"Created AlloyDB engine for {self.inst_uri} and user: {user}")
        return engine

    def _create_engine(self):
        if not AlloyDBEngine:
                log.error("Can't create AlloyDBEngine - install via `pip install sunholo[gcp,database]`")
                raise ValueError("Can't import AlloyDBEngine")

        log.info(f"Inititaing AlloyDB Langchain engine for database: {self.database}")

        from google.cloud.alloydb.connector import IPTypes
        engine = AlloyDBEngine.from_instance(
            project_id=self.config["project_id"],
            region=self.config["region"],
            cluster=self.config["cluster"],
            instance=self.config["instance"],
            database=self.database,
            ip_type=self.config.get("ip_type") or IPTypes.PRIVATE
        )
        self._loop = engine._loop

        log.info(f"Created AlloyDB engine for {engine}")

        return engine
    
    def _get_embedder(self):
        return get_embeddings(self.vector_name)
    
    def get_vectorstore(self, vector_name:str=None):
        if self.engine_type != "langchain":
            raise ValueError("Not available using pg8000 engine")
        
        if vector_name:
            self.vector_name = vector_name

        if self.vector_name is None:
            raise ValueError("No vectorname found - init with ConfigManager?")
        
        vector_size = get_vector_size(self.vector_name)
        table_name = f"{self.vector_name}_vectorstore_{vector_size}"

        log.info(f"Initialised AlloyDBClient with AlloyDBVectorStore: {table_name}")
        self.vectorstore = AlloyDBVectorStore.create_sync(
                engine=self.engine,
                table_name=table_name,
                embedding_service=self._get_embedder(),
                metadata_columns=["source", "docstore_doc_id"]
                #metadata_columns=["source", "eventTime"]
            )
        
        return self.vectorstore
    
    def _similarity_search(self, query, source_filter:str="", free_filter:str=None, vector_name:str=None):

        self.get_vectorstore(vector_name) 

        if free_filter is None:
            source_filter_cmd = f"source %LIKE% {source_filter}" if source_filter else None
        else:
            source_filter_cmd = free_filter

        log.info(f"Similarity search for {query} and {source_filter_cmd}")       

        return query, source_filter_cmd

    def similarity_search(self, query:str, source_filter:str="", free_filter:str=None, k:int=5, vector_name:str=None):

        query, source_filter_cmd = self._similarity_search(query, 
                                                           source_filter=source_filter, 
                                                           free_filter=free_filter, 
                                                           vector_name=vector_name)    

        return self.vectorstore.similarity_search(query, filter=source_filter_cmd, k=k)

    async def asimilarity_search(self, query:str, source_filter:str="", free_filter:str=None, k:int=5, vector_name:str=None):

        query, source_filter_cmd = self._similarity_search(query, 
                                                           source_filter=source_filter, 
                                                           free_filter=free_filter, 
                                                           vector_name=vector_name)     

        return await self.vectorstore.asimilarity_search(query, filter=source_filter_cmd, k=k)

    def execute_sql(self, sql_statement):
        log.info(f"Executing sync SQL statement: {sql_statement}")
        if self.engine_type == "pg8000":
            return self._execute_sql_pg8000(sql_statement)
        elif self.engine_type == "langchain":
            return self._execute_sql_langchain(sql_statement)
    
    def _execute_sql_langchain(self, sql_statement):
        return self.engine._fetch(query = sql_statement)

    def _execute_sql_pg8000(self, sql_statement):
        """Executes a given SQL statement with error handling.

         - sql_statement (str): The SQL statement to execute.
         - Returns: The result of the execution, if any.
        """
        sql_ = sqlalchemy.text(sql_statement)
        result = None
        with self.engine.connect() as conn:
            try:
                log.info(f"Executing SQL statement: {sql_}")
                result = conn.execute(sql_)
            except DatabaseError as e:
                if "already exists" in str(e):
                    log.warning(f"Error ignored: {str(e)}. Assuming object already exists.")
                else:
                    raise  
            finally:
                conn.close()

        return result
    
    async def execute_sql_async(self, sql_statement):
        log.info(f"Executing async SQL statement: {sql_statement}")
        if self.engine_type == "pg8000":
            result = await self._execute_sql_async_pg8000(sql_statement)
        elif self.engine_type == "langchain":
            result = await self._execute_sql_async_langchain(sql_statement)
        
        return result

    async def _execute_sql_async_langchain(self, sql_statement):
        return await self.engine._afetch(query = sql_statement)
        
    async def _execute_sql_async_pg8000(self, sql_statement):
        """Executes a given SQL statement asynchronously with error handling."""
        sql_ = sqlalchemy.text(sql_statement)
        result = None
        async with self.engine.connect() as conn:
            try:
                log.info(f"Executing SQL statement asynchronously: {sql_}")
                result = await conn.execute(sql_)
            except DatabaseError as e:
                if "already exists" in str(e):
                    log.warning(f"Error ignored: {str(e)}. Assuming object already exists.")
                else:
                    raise
            finally:
                await conn.close()

        return result
    
    def get_document_from_docstore(self, source:str, vector_name):
        query = self._get_document_from_docstore(source, vector_name)

        return self.execute_sql(query)

    async def get_document_from_docstore_async(self, source:str, vector_name:str):
        query = self._get_document_from_docstore(source, vector_name)

        document = await self.execute_sql_async(query)

        return document
    
    def _get_document_from_docstore(self, source:str, vector_name:str):
        if not isinstance(source, str):
            raise ValueError("The 'source' parameter must be a single string, not a list of strings or other iterable.")

        table_name = f"{vector_name}_docstore"
        #doc_id = generate_uuid_from_object_id(source)

        query = f"""
            SELECT page_content, source, langchain_metadata, images_gsurls, doc_id::text as doc_id
            FROM "{table_name}"
            WHERE source = '{source}'
            LIMIT 500;
        """

        return query

    def _get_document_via_docid(self, source:str, vector_name:str, doc_id: str):
        if not isinstance(source, str):
            raise ValueError("The 'source' parameter must be a single string, not a list of strings or other iterable.")

        table_name = f"{vector_name}_docstore"
        if not doc_id:
            doc_id = generate_uuid_from_object_id(source)

        query = f"""
            SELECT page_content, source, langchain_metadata, images_gsurls, doc_id::text as doc_id
            FROM "{table_name}"
            WHERE doc_id = '{doc_id}'
            LIMIT 50;
        """

        return query

    async def get_sources_from_docstore_async(self, sources, vector_name, search_type="OR", just_source_name=False):
        """Fetches sources from the docstore asynchronously."""
        if just_source_name:
            query = self._list_sources_from_docstore(sources, vector_name=vector_name, search_type=search_type)
        else:
            query = self._get_sources_from_docstore(sources, vector_name=vector_name, search_type=search_type)

        if not query:
            return []

        documents = await self.execute_sql_async(query)
        return documents

    def get_sources_from_docstore(self, sources, vector_name, search_type="OR", just_source_name=False):
        """Fetches sources from the docstore."""
        if just_source_name:
            query = self._list_sources_from_docstore(sources, vector_name=vector_name, search_type=search_type)
        else:
            query = self._get_sources_from_docstore(sources, vector_name=vector_name, search_type=search_type)

        if not query:
            return []

        documents = self.execute_sql(query)

        return documents

    def _get_sources_from_docstore(self, sources, vector_name, search_type="OR"):
        """Helper function to build the SQL query for fetching sources."""
        if not sources:
            log.warning("No sources found for alloydb fetch")
            return ""

        table_name = f"{vector_name}_docstore"

        conditions = self._and_or_ilike(sources, search_type=search_type)

        query = f"""
            SELECT * 
            FROM {table_name}
            WHERE {conditions}
            ORDER BY langchain_metadata->>'objectId' ASC
            LIMIT 50;
        """

        return query

    def _list_sources_from_docstore(self, sources, vector_name, search_type="OR"):
        """Helper function to build the SQL query for listing sources."""
        table_name = f"{vector_name}_docstore"

        if sources:
            conditions = self._and_or_ilike(sources, search_type=search_type)
            query = f"""
                SELECT DISTINCT langchain_metadata->>'objectId' AS objectId
                FROM {table_name}
                WHERE {conditions}
                ORDER BY langchain_metadata->>'objectId' ASC
                LIMIT 500;
            """
        else:
            query = f"""
                SELECT DISTINCT langchain_metadata->>'objectId' AS objectId
                FROM {table_name}
                ORDER BY langchain_metadata->>'objectId' ASC
                LIMIT 500;
            """

        return query

    @staticmethod
    def _and_or_ilike(sources, search_type="OR", operator="ILIKE"):
        unique_sources = set(sources)
        # Choose the delimiter based on the search_type argument
        delimiter = ' AND ' if search_type.upper() == "AND" else ' OR '

        # Build the conditional expressions based on the chosen delimiter
        conditions = delimiter.join(f"TRIM(source) {operator} '%{source}%'" for source in unique_sources)
        if not conditions:
            log.warning("Alloydb doc query found no like_patterns")
            return []
        
        return conditions

    def delete_sources_from_alloydb(self, sources, vector_name):
        """
        Deletes from both vectorstore and docstore
        """

        vector_length = get_vector_size(vector_name)

        conditions = self._and_or_ilike(sources, operator="=")

        if not conditions:
            log.warning("No conditions were specified, not deleting whole table!")
            return False

        query = f"""
            DELETE FROM {vector_name}_docstore
            WHERE {conditions};
            DELETE FROM {vector_name}_vectorstore_{vector_length}
            WHERE {conditions}
        """

        return self.execute_sql(query)

    def create_database(self, database_name):
        self.execute_sql(f'CREATE DATABASE "{database_name}"')

    def fetch_owners(self):
        owners = self.execute_sql('SELECT table_schema, table_name, privilege_type FROM information_schema.table_privileges')
        for row in owners:
            print(f"Schema: {row[0]}, Table: {row[1]}, Privilege: {row[2]}")
        return owners

    def create_schema(self, schema_name="public"):
        self.execute_sql(f'CREATE SCHEMA IF NOT EXISTS {schema_name};')

    def grant_schema_permissions(self, schema_name, users):
        for user in users:
            self.execute_sql(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema_name} TO "{user}";')
            self.execute_sql(f'GRANT USAGE, CREATE ON SCHEMA {schema_name} TO "{user}";')
            self.execute_sql(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{user}";')
            self.execute_sql(f'GRANT USAGE ON SCHEMA information_schema TO "{user}";')
            self.execute_sql(f'GRANT SELECT ON information_schema.columns TO "{user}";')
    
    def grant_table_permissions(self, table_name, users):
        for user in users:
            self.execute_sql(f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "{table_name}" TO "{user}";')
    
    def create_tables(self, vector_name, users):
        self.create_docstore_table(vector_name, users)
        self.create_vectorstore_table(vector_name, users)

    def create_docstore_table(self, vector_name: str, users):
        table_name = f"{vector_name}_vectorstore"
        sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" 
        (page_content TEXT, doc_id UUID, source TEXT, images_gsurls JSONB, chunk_metadata JSONB, langchain_metadata JSONB)
        '''
        self.execute_sql(sql)

        self.grant_table_permissions(table_name, users)

    def create_vectorstore_table(self, vector_name: str, users):
        from .database import get_vector_size
        vector_size = get_vector_size(vector_name)
        vectorstore_id = f"{vector_name}_{type}_{vector_size}"

        sql = f'''
        CREATE TABLE IF NOT EXISTS "{vectorstore_id}" (
        langchain_id UUID NOT NULL,
        content TEXT NOT NULL,
        embedding vector NOT NULL,
        source TEXT,
        langchain_metadata JSONB,
        docstore_doc_id UUID,
        eventTime TIMESTAMPTZ
        );
        '''
        self.execute_sql(sql)

        self.grant_table_permissions(vectorstore_id, users)