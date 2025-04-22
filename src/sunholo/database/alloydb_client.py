import os
try:
    import pg8000
    import sqlalchemy
    from sqlalchemy.exc import DatabaseError, ProgrammingError
    from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBVectorStore
except ImportError:
    AlloyDBEngine = None
    pass

import json
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
                 config:ConfigManager=None,
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
        
        alloydb_config = None
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
        if ALLOYDB_DB is None and alloydb_config and alloydb_config.get("database") is None:
            log.warning("Could not locate ALLOYDB_DB environment variable or 'alloydb_config.database'")
        
        if alloydb_config:
            self.database = alloydb_config.get("database") or ALLOYDB_DB or db
        else:
            self.database = ALLOYDB_DB or db

        if not self.database:
            raise ValueError("Could not derive a database to query")

        self.user = user
        self.password = password
        self.inst_url = ""
        if user:
            log.info(f"User specified {user} - using pg8000 engine")
            self.inst_url = self._build_instance_uri(project_id, region, cluster_name, instance_name)
            self.engine = self._create_engine_from_pg8000(user, password, self.database)
            self.engine_type = "pg8000"
            from google.cloud.alloydb.connector import Connector
            self.connector = Connector()
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
                self.inst_url,
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

        log.info(f"Created AlloyDB engine for {self.inst_url} and user: {user}")
        return engine

    def _create_engine(self):
        if not AlloyDBEngine:
                log.error("Can't create AlloyDBEngine - install via `pip install sunholo[gcp,database]`")
                raise ValueError("Can't import AlloyDBEngine")

        log.info(f"Inititaing AlloyDB Langchain engine for database: {self.database} with config: {self.config}")

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
            source_filter_cmd = f"source ILIKE '%{source_filter}%'" if source_filter else None
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
    
    def create_index(self, vectorstore=None):
        from langchain_google_alloydb_pg.indexes import IVFFlatIndex

        index = IVFFlatIndex()
        vs = vectorstore or self.vectorstore

        return vs.apply_vector_index(index)
    
    def refresh_index(self, vectorstore=None):
        vs = vectorstore or self.vectorstore

        return vs.reindex()

    def execute_sql(self, sql_statement):
        log.info(f"Executing sync SQL statement: {sql_statement}")
        if self.engine_type == "pg8000":
            return self._execute_sql_pg8000(sql_statement)
        elif self.engine_type == "langchain":
            return self._execute_sql_langchain(sql_statement)
    
    def _execute_sql_langchain(self, sql_statement):
        return self.engine._fetch(query = sql_statement)

    def _execute_sql_pg8000(self, sql_statement, params=None):
        """
        Executes a given SQL statement with error handling.

        Args:
            sql_statement (str): The SQL statement to execute.
            params (dict or list, optional): Parameters for the SQL statement.
            
        Returns:
            The result of the execution, if any.
        """
        sql_ = sqlalchemy.text(sql_statement)
        result = None
        with self.engine.connect() as conn:
            try:
                log.info(f"Executing SQL statement: {sql_}")
                if params:
                    result = conn.execute(sql_, params)
                else:
                    result = conn.execute(sql_)
            except DatabaseError as e:
                if "already exists" in str(e):
                    log.warning(f"Error ignored: {str(e)}. Assuming object already exists.")
                else:
                    log.error(f"Database error: {e}, SQL: {sql_statement}, Params: {params}")
                    raise  
            finally:
                conn.close()

        return result
    
    async def execute_sql_async(self, sql_statement):
        log.info(f"Executing async SQL statement: {sql_statement}")
        if self.engine_type == "pg8000":
            # dont use async???
            result = await self._execute_sql_async_pg8000(sql_statement)
        elif self.engine_type == "langchain":
            result = await self._execute_sql_async_langchain(sql_statement)
        
        return result

    async def _execute_sql_async_langchain(self, sql_statement):
        return await self.engine._afetch(query = sql_statement)
        
    async def _execute_sql_async_pg8000(self, sql_statement, values=None):
        """Executes a given SQL statement asynchronously with error handling.
        
        Args:
            sql_statement (str): The SQL statement to execute
            values (list, optional): Values for parameterized query
            
        Returns:
            Result of SQL execution
        """
        sql_ = sqlalchemy.text(sql_statement)
        result = None
        
        # IMPORTANT: Don't use await here, the engine.connect() is synchronous
        conn = self.engine.connect()
        try:
            log.info(f"Executing SQL statement asynchronously: {sql_}")
            if values:
                result = conn.execute(sql_, values)
            else:
                result = conn.execute(sql_)
            
            # Explicitly commit transaction
            await conn.commit()
        except DatabaseError as e:
            if "already exists" in str(e):
                log.warning(f"Error ignored: {str(e)}. Assuming object already exists.")
            else:
                raise
        finally:
            # Close connection only here, not inside the context manager
            conn.close()

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
            WHERE source ILIKE '%{source}%'
            LIMIT 1000;
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
            LIMIT 500;
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
            WITH ranked_sources AS (
            SELECT *,
                    ROW_NUMBER() OVER (PARTITION BY source ORDER BY doc_id) as chunk_num
            FROM {table_name}
            WHERE {conditions}
            )
            SELECT *
            FROM ranked_sources
            ORDER BY source ASC, chunk_num ASC
            LIMIT 1000;
        """

        return query

    def _list_sources_from_docstore(self, sources, vector_name, search_type="OR"):
        """Helper function to build the SQL query for listing sources."""
        table_name = f"{vector_name}_docstore"

        if sources:
            conditions = self._and_or_ilike(sources, search_type=search_type)
            query = f"""
                SELECT DISTINCT source AS objectId
                FROM {table_name}
                WHERE {conditions}
                ORDER BY source ASC
                LIMIT 500;
            """
        else:
            query = f"""
                SELECT DISTINCT source AS objectId
                FROM {table_name}
                GROUP BY source
                ORDER BY source ASC
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
        embedding vector({vector_size}) NOT NULL,
        source TEXT,
        langchain_metadata JSONB,
        docstore_doc_id UUID,
        eventTime TIMESTAMPTZ
        );
        '''
        self.execute_sql(sql)

        self.grant_table_permissions(vectorstore_id, users)

    async def check_connection(self):
        """
        Checks if the database connection is still valid.
        
        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            # For pg8000 engine, use synchronous connection
            if self.engine_type == "pg8000":
                # Use direct synchronous query
                with self.engine.connect() as conn:
                    conn.execute(sqlalchemy.text("SELECT 1"))
                return True
            else:
                # For langchain, use async connection
                await self._execute_sql_async_langchain("SELECT 1")
                return True
        except Exception as e:
            log.warning(f"Database connection check failed: {e}")
            return False

    async def ensure_connected(self):
        """
        Ensures the database connection is valid, attempting to reconnect if necessary.
        
        Returns:
            bool: True if connection is valid or reconnection successful, False otherwise
        """
        if await self.check_connection():
            return True
            
        try:
            # Attempt to reconnect - implementation depends on your database driver
            if self.engine_type == "pg8000":
                # Re-create the engine
                self.engine = self._create_engine_from_pg8000(self.user, self.password, self.database)
            elif self.engine_type == "langchain":
                # Re-create the engine
                self.engine = self._create_engine()
                
            log.info("Successfully reconnected to AlloyDB")
            return True
        except Exception as e:
            log.error(f"Failed to reconnect to AlloyDB: {e}")
            return False

    async def close(self):
        """
        Properly close the database connection.
        """
        try:
            if self.engine_type == "pg8000":
                # Close engine or connector
                if hasattr(self, 'connector'):
                    await self.connector.close()
            # For langchain engine, additional cleanup might be needed
            log.info("Closed AlloyDB connection")
        except Exception as e:
            log.warning(f"Error closing AlloyDB connection: {e}")

    async def create_table_from_schema(self, table_name: str, schema_data: dict, users: list = None):
        """
        Creates or ensures a table exists based on the structure of the provided schema data,
        with special handling for expandable lists.
        
        Args:
            table_name (str): Name of the table to create
            schema_data (dict): Data structure that matches the expected schema
            users (list, optional): List of users to grant permissions to
            
        Returns:
            Result of SQL execution
        """
        # Generate column definitions from schema data
        columns = []
        
        for key, value in schema_data.items():
            # Check if this is a specially marked expandable list
            if isinstance(value, dict) and value.get("__is_expandable_list__", False):
                # Handle expandable lists - we need to examine the first item to determine column types
                items = value.get("items", [])
                
                # Add an index column for this list
                columns.append(f'"{key}_index" INTEGER')
                
                if items and isinstance(items[0], dict):
                    # If the first item is a dictionary, we need to create columns for all its keys
                    sample_item = items[0]
                    
                    # Create columns for all keys in the sample item
                    for item_key, item_value in sample_item.items():
                        column_key = f"{key}_{item_key}"
                        column_type = self._get_sql_type(item_value)
                        columns.append(f'"{column_key}" {column_type}')
                else:
                    # If items are simple values, just add a column for the list key itself
                    column_type = self._get_sql_type(items[0] if items else None)
                    columns.append(f'"{key}" {column_type}')
            else:
                # Regular handling for non-list fields
                column_type = self._get_sql_type(value)
                columns.append(f'"{key}" {column_type}')
        
        # Add metadata columns
        columns.extend([
            '"source" TEXT',
            '"extraction_date" TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP',
            '"extraction_backend" TEXT',
            '"extraction_model" TEXT'
        ])
        
        # Create SQL statement for table creation
        columns_sql = ", ".join(columns)
        sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id SERIAL PRIMARY KEY,
            {columns_sql}
        )
        '''
        
        # Execute SQL to create table based on engine type
        if self.engine_type == "pg8000":
            # Use the synchronous method for pg8000
            result = self._execute_sql_pg8000(sql)
        else:
            # Use the async method for langchain
            result = await self._execute_sql_async_langchain(sql)
        
        log.info(f"Created or ensured table {table_name} exists")
        
        # Grant permissions if users are provided
        if users:
            for user in users:
                grant_sql = f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "{table_name}" TO "{user}";'
                if self.engine_type == "pg8000":
                    self._execute_sql_pg8000(grant_sql)
                else:
                    await self._execute_sql_async_langchain(grant_sql)
        
        return result

    def _get_sql_type(self, value):
        """
        Helper method to determine SQL type from a Python value.
        
        Args:
            value: The value to determine the column type
            
        Returns:
            str: SQL type
        """
        if value is None:
            # For unknown types (None), default to TEXT
            return "TEXT"
        elif isinstance(value, dict):
            # For nested objects, store as JSONB
            return "JSONB"
        elif isinstance(value, list):
            # For arrays, store as JSONB
            return "JSONB"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "NUMERIC"
        elif isinstance(value, bool):
            return "BOOLEAN"
        else:
            # Default to TEXT for strings and other types
            return "TEXT"

    def _flatten_dict_for_schema(self, nested_dict, parent_key='', separator='.'):
        """
        Flatten a nested dictionary for schema creation.
        
        Args:
            nested_dict (dict): The nested dictionary to flatten
            parent_key (str): The parent key for the current recursion level
            separator (str): The separator to use between key levels
            
        Returns:
            dict: A flattened dictionary
        """
        flattened = {}
        
        for key, value in nested_dict.items():
            # Create the new key with parent_key if it exists
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            # If value is a dictionary, recursively flatten it
            if isinstance(value, dict):
                flattened.update(self._flatten_dict_for_schema(value, new_key, separator))
            else:
                # For simple values, just add them with the new key
                flattened[new_key] = value
                
        return flattened

    def _flatten_dict(self, nested_dict, parent_key='', separator='.'):
        """
        Flatten a nested dictionary into a single-level dictionary with dot notation for keys.
        
        Args:
            nested_dict (dict): The nested dictionary to flatten
            parent_key (str): The parent key for the current recursion level
            separator (str): The separator to use between key levels (default: '.')
            
        Returns:
            dict: A flattened dictionary with special handling for lists
        """
        flattened = {}
        
        for key, value in nested_dict.items():
            # Create the new key with parent_key if it exists
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            # If value is a dictionary, recursively flatten it
            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, new_key, separator))
            # Handle lists containing dictionaries or other values
            elif isinstance(value, list):
                # Mark lists for special processing during database insertion
                # We'll use a special format to indicate this is a list that needs expansion
                flattened[new_key] = {
                    "__is_expandable_list__": True,
                    "items": value
                }
            else:
                # For simple values, just add them with the new key
                flattened[new_key] = value
                
        return flattened

    async def write_data_to_table(self, table_name: str, data: dict, metadata: dict = None):
        """
        Writes data to the specified table, with special handling for expandable lists.
        
        Args:
            table_name (str): Name of the table
            data (dict): Data to write to the table
            metadata (dict, optional): Additional metadata to include
                
        Returns:
            List of results from SQL executions
        """
        # Find any expandable lists in the data
        expandable_lists = {}
        regular_data = {}
        
        for key, value in data.items():
            if isinstance(value, dict) and value.get("__is_expandable_list__", False):
                expandable_lists[key] = value["items"]
            else:
                regular_data[key] = value
        
        # If no expandable lists are found, do a simple insert
        if not expandable_lists:
            return await self._insert_single_row(table_name, regular_data, metadata)
        
        # For expandable lists, we need to create multiple rows
        results = []
        
        # Create combinations of rows based on expandable lists
        if expandable_lists:
            # Get the first expandable list to start with
            primary_list_key = next(iter(expandable_lists))
            primary_list = expandable_lists[primary_list_key]
            
            log.info(f"Expanding list '{primary_list_key}' with {len(primary_list)} items into separate rows")
            
            # For each item in the primary list, create a new row
            for item_idx, item in enumerate(primary_list):
                # Create a copy of the regular data
                row_data = dict(regular_data)
                
                # Add the current item from the primary list
                if isinstance(item, dict):
                    # If it's a dictionary, flatten it with the primary key as prefix
                    flattened_item = {}
                    for k, v in item.items():
                        flattened_key = f"{primary_list_key}_{k}"
                        flattened_item[flattened_key] = v
                    
                    # Update row data with flattened item
                    row_data.update(flattened_item)
                else:
                    # If it's a simple value, just add it with the list key
                    row_data[primary_list_key] = item
                
                # Add item index for reference
                row_data[f"{primary_list_key}_index"] = item_idx
                
                # Insert this row
                result = await self._insert_single_row(table_name, row_data, metadata)
                results.append(result)
            
            return results
        
        # If we somehow get here (shouldn't happen), fall back to single row insert
        return await self._insert_single_row(table_name, regular_data, metadata)


    async def _insert_single_row(self, table_name: str, data: dict, metadata: dict = None, primary_key_column:str = "id"):
        """
        Inserts a single row of data into the specified table.
        
        Args:
            table_name (str): Name of the table
            data (dict): Data to write to the table
            metadata (dict, optional): Additional metadata to include
            
        Returns:
            Result of SQL execution
        """
        
        # Create copies to avoid modifying the original data
        insert_data = dict(data)
        
        # Add metadata if provided
        if metadata:
            insert_data["source"] = metadata.get("objectId", metadata.get("source", "not-in-metadata"))
            insert_data["extraction_backend"] = metadata.get("extraction_backend", "not-in-metadata")
            insert_data["extraction_model"] = metadata.get("extraction_model", "not-in-metadata")
        
        # Prepare column names and values for SQL
        columns = [f'"{key}"' for key in insert_data.keys()]
        
        # Process values
        processed_values = {}
        for i, (key, value) in enumerate(insert_data.items()):
            # Create a unique parameter name
            param_name = f"param_{i}"
            # For JSON values, convert to string
            if isinstance(value, (dict, list)):
                processed_values[param_name] = json.dumps(value)
            else:
                processed_values[param_name] = value
        
        # Create placeholders using named parameters
        placeholders = [f":{param_name}" for param_name in processed_values.keys()]
        
        # Create SQL statement for insertion
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(placeholders)
        
        sql = f'''
        INSERT INTO "{table_name}" ({columns_str})
        VALUES ({placeholders_str})
        RETURNING {primary_key_column}
        '''
        
        # Execute SQL to insert data based on engine type
        if self.engine_type == "pg8000":
            # Use the synchronous method for pg8000 with properly formatted parameters
            result = self._execute_sql_pg8000(sql, processed_values)
        else:
            # Use the async method for langchain
            result = await self._execute_sql_async_langchain(sql, processed_values)
        
        log.info(f"Inserted data into table {table_name}")
        
        return result

    async def update_row(self, table_name: str, primary_key_column: str, primary_key_value: str, 
                        update_data: dict, condition: str = None):
        """
        Updates a row in the specified table based on the primary key.
        
        Args:
            table_name (str): Name of the table to update
            primary_key_column (str): Name of the primary key column (e.g., 'acdid')
            primary_key_value (str): Value of the primary key for the row to update
            update_data (dict): Dictionary containing column names and values to update
            condition (str, optional): Additional condition for the WHERE clause
            
        Returns:
            Result of SQL execution
        """
        if not update_data:
            raise ValueError("No update data provided")
        
        # Generate SET clause parts
        set_parts = []
        processed_values = {}
        
        for i, (key, value) in enumerate(update_data.items()):
            # Create a unique parameter name
            param_name = f"param_{i}"
            # For JSON values, convert to string
            if isinstance(value, (dict, list)):
                processed_values[param_name] = json.dumps(value)
            else:
                processed_values[param_name] = value
            
            set_parts.append(f'"{key}" = :{param_name}')
        
        # Create the WHERE clause
        where_clause = f'"{primary_key_column}" = :pk_value'
        processed_values['pk_value'] = primary_key_value
        
        if condition:
            where_clause += f" AND ({condition})"
        
        # Construct the SQL statement
        set_clause = ", ".join(set_parts)
        sql = f'UPDATE "{table_name}" SET {set_clause} WHERE {where_clause} RETURNING {primary_key_column}'
        
        log.info(f"Executing update on {table_name} for {primary_key_column}={primary_key_value}")
        
        # Execute SQL based on engine type
        if self.engine_type == "pg8000":
            # Use the synchronous method for pg8000
            result = self._execute_sql_pg8000(sql, processed_values)
        else:
            # Use the async method for langchain
            result = await self._execute_sql_async_langchain(sql, processed_values)
        
        log.info(f"Updated row in {table_name} with {primary_key_column}={primary_key_value}")
        
        return result

    async def check_row(self, table_name: str, primary_key_column: str, primary_key_value: str, 
                    columns: list = None, condition: str = None):
        """
        Retrieves a row from the specified table based on the primary key.
        
        Args:
            table_name (str): Name of the table to query
            primary_key_column (str): Name of the primary key column (e.g., 'id')
            primary_key_value (str): Value of the primary key for the row to retrieve
            columns (list, optional): List of column names to retrieve. If None, retrieves all columns
            condition (str, optional): Additional condition for the WHERE clause
            
        Returns:
            The row data if found, None otherwise
        """
        # Determine which columns to select
        if columns and isinstance(columns, list):
            columns_str = ", ".join([f'"{col}"' for col in columns])
        else:
            columns_str = "*"  # Select all columns if none specified
        
        # Create the WHERE clause
        where_clause = f'"{primary_key_column}" = :pk_value'
        values = {'pk_value': primary_key_value}
        
        if condition:
            where_clause += f" AND ({condition})"
        
        # Construct the SQL statement
        sql = f'SELECT {columns_str} FROM "{table_name}" WHERE {where_clause} LIMIT 1'
        
        log.info(f"Checking row in {table_name} with {primary_key_column}={primary_key_value}")
        
        # Execute SQL based on engine type
        try:
            if self.engine_type == "pg8000":
                # Use the synchronous method for pg8000
                result = self._execute_sql_pg8000(sql, values)
                # Extract the row data from the result
                if result and hasattr(result, 'fetchone'):
                    row = result.fetchone()
                    if row:
                        # If we have column names, convert to dictionary
                        if hasattr(result, 'keys'):
                            column_names = result.keys()
                            return dict(zip(column_names, row))
                        return row
                return None
            else:
                # Use the async method for langchain
                result = await self._execute_sql_async_langchain(sql, values)
                # For langchain engine, check result format and return first row if exists
                if result and len(result) > 0:
                    return result[0]
                return None
        except Exception as e:
            log.error(f"Error checking row: {e}")
            return None
    
    async def get_table_columns(self, table_name, schema="public"):
        """
        Fetch column information for an existing table.
        
        Args:
            table_name (str): The table name to get columns for
            schema (str): Database schema, defaults to "public"
            
        Returns:
            List[dict]: List of column information dictionaries with keys:
                - name: column name
                - type: PostgreSQL data type
                - is_nullable: whether the column allows NULL values
                - default: default value if any
        """
        try:
            query = f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default,
                character_maximum_length
            FROM 
                information_schema.columns 
            WHERE 
                table_name = '{table_name}'
                AND table_schema = '{schema}'
            ORDER BY 
                ordinal_position;
            """
            
            if self.engine_type == "pg8000":
                result = self._execute_sql_pg8000(query)
                rows = result.fetchall() if hasattr(result, 'fetchall') else result
            else:
                rows = await self._execute_sql_async_langchain(query)
            
            columns = []
            for row in rows:
                column_info = {
                    "name": row[0],
                    "type": row[1],
                    "is_nullable": row[2] == "YES",
                    "default": row[3],
                    "max_length": row[4]
                }
                columns.append(column_info)
            
            log.info(f"Retrieved {len(columns)} columns for table '{table_name}'")
            return columns
        
        except Exception as e:
            log.error(f"Error getting table columns: {e}")
            return []

    def map_data_to_columns(self, data, column_info, case_sensitive=False):
        """
        Map data dictionary to available table columns, handling case sensitivity.
        
        Args:
            data (dict): Dictionary of data to map
            column_info (list): List of column information dictionaries from get_table_columns
            case_sensitive (bool): Whether to match column names case-sensitively
            
        Returns:
            dict: Filtered data dictionary with only columns that exist in the table
        """
        if not column_info:
            return data  # No column info, return original data
        
        # Create lookup dictionaries for columns
        columns = {}
        columns_lower = {}
        
        for col in column_info:
            col_name = col["name"]
            columns[col_name] = col
            columns_lower[col_name.lower()] = col_name
        
        # Filter and map the data
        filtered_data = {}
        for key, value in data.items():
            if case_sensitive:
                # Case-sensitive matching
                if key in columns:
                    filtered_data[key] = value
            else:
                # Case-insensitive matching
                key_lower = key.lower()
                if key_lower in columns_lower:
                    # Use the original column name from the database
                    original_key = columns_lower[key_lower]
                    filtered_data[original_key] = value
        
        return filtered_data

    def safe_convert_value(self, value, target_type):
        """
        Safely convert a value to the target PostgreSQL type.
        Handles various formats and placeholder values.
        
        Args:
            value: The value to convert
            target_type (str): PostgreSQL data type name
            
        Returns:
            The converted value appropriate for the target type, or None if conversion fails
        """
        if value is None:
            return None
        
        # Handle placeholder values
        if isinstance(value, str):
            if value.startswith("No ") or value.lower() in ("none", "n/a", "null", ""):
                # Special placeholders are converted to None for most types
                return None
        
        try:
            # Handle different target types
            if target_type in ("integer", "bigint", "smallint"):
                if isinstance(value, (int, float)):
                    return int(value)
                elif isinstance(value, str) and value.strip():
                    # Try to extract a number from the string
                    cleaned = value.replace(',', '')
                    # Extract the first number if there's text
                    import re
                    match = re.search(r'[-+]?\d+', cleaned)
                    if match:
                        return int(match.group())
                return None
                
            elif target_type in ("numeric", "decimal", "real", "double precision"):
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str) and value.strip():
                    # Remove currency symbols and try to convert
                    cleaned = value.replace('$', '').replace('€', '').replace('£', '')
                    cleaned = cleaned.replace(',', '.')
                    # Extract the first number if there's text
                    import re
                    match = re.search(r'[-+]?\d+(\.\d+)?', cleaned)
                    if match:
                        return float(match.group())
                return None
                
            elif target_type == "boolean":
                if isinstance(value, bool):
                    return value
                elif isinstance(value, (int, float)):
                    return bool(value)
                elif isinstance(value, str):
                    value_lower = value.lower()
                    if value_lower in ("true", "t", "yes", "y", "1"):
                        return True
                    elif value_lower in ("false", "f", "no", "n", "0"):
                        return False
                return None
                
            elif target_type.startswith("timestamp"):
                if isinstance(value, str):
                    # For dates, keep the string format - DB driver will handle conversion
                    return value
                # Other types, just return as is
                return value
                
            elif target_type == "jsonb" or target_type == "json":
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                elif isinstance(value, str):
                    # Validate it's valid JSON
                    try:
                        json.loads(value)
                        return value
                    except:
                        return None
                return None
                
            else:
                # For text and other types, convert to string
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                elif value is not None:
                    return str(value)
                return None
                    
        except Exception as e:
            log.debug(f"Conversion error for value '{value}' to {target_type}: {e}")
            return None

    async def insert_rows_safely(self, table_name, rows, metadata=None, continue_on_error=False, primary_key_column="id"  # Specify the correct primary key column here
):
        """
        Insert multiple rows into a table with error handling for individual rows.
        
        Args:
            table_name (str): The table to insert into
            rows (list): List of dictionaries containing row data
            metadata (dict, optional): Additional metadata to include in each row
            continue_on_error (bool): Whether to continue if some rows fail
            primary_key_column (str): The primary key in the table, default 'id'
            
        Returns:
            dict: {
                'success': bool,
                'total_rows': int,
                'inserted_rows': int,
                'failed_rows': int,
                'errors': list of errors with row data
            }
        """
        if not rows:
            return {'success': True, 'total_rows': 0, 'inserted_rows': 0, 'failed_rows': 0, 'errors': []}
        
        # Get table columns for mapping and type conversion
        columns = await self.get_table_columns(table_name)
        column_map = {col['name']: col for col in columns}
        column_map_lower = {col['name'].lower(): col for col in columns}
        
        results = {
            'success': True,
            'total_rows': len(rows),
            'inserted_rows': 0,
            'failed_rows': 0,
            'errors': [],
            'return_ids': []
        }
        
        for i, row in enumerate(rows):
            try:
                # Map row data to actual table columns
                filtered_row = {}
                
                # First, do case-insensitive mapping
                for key, value in row.items():
                    key_lower = key.lower()
                    if key_lower in column_map_lower:
                        col_info = column_map_lower[key_lower]
                        col_name = col_info['name']  # Use the correct case from DB
                        col_type = col_info['type']
                        
                        # Try to convert value to the appropriate type
                        converted_value = self.safe_convert_value(value, col_type)
                        filtered_row[col_name] = converted_value
                
                # Add metadata if provided
                if metadata:
                    for key, value in metadata.items():
                        key_lower = key.lower()
                        if key_lower in column_map_lower:
                            col_name = column_map_lower[key_lower]['name']
                            filtered_row[col_name] = value
                
                # Insert the row
                result = await self._insert_single_row(table_name, filtered_row, primary_key_column=primary_key_column)
                result_ids = []
                for res in result:
                    result_ids.append(str(res))
                results['return_ids'].append(result_ids)
                results['inserted_rows'] += 1
                
            except Exception as e:
                error_info = {
                    'row_index': i,
                    'error': str(e),
                    'row_data': row
                }
                results['errors'].append(error_info)
                results['failed_rows'] += 1
                
                log.error(f"Error inserting row {i}: {e} for data: {row}")
                
                if not continue_on_error:
                    results['success'] = False
                    return results
        
        # Overall success is true if any rows were inserted successfully
        results['success'] = results['inserted_rows'] > 0
        return results

    async def create_table_with_columns(self, table_name, column_definitions, if_not_exists=True, primary_key_column="id"):
        """
        Create a table with explicit column definitions.
        
        Args:
            table_name (str): The name of the table to create
            column_definitions (list): List of column definition dictionaries:
                - name: Column name
                - type: PostgreSQL data type
                - nullable: Whether column allows NULL (default True)
                - default: Default value expression (optional)
                - primary_key: Whether this is a primary key (default False)
            if_not_exists (bool): Whether to use IF NOT EXISTS clause
            primary_key_column (str): default name of primary key if not specified in column_definitions
            
            
        Returns:
            Result of the execution
        """
        if not column_definitions:
            raise ValueError("No column definitions provided")
        
        # Generate column definition strings
        column_strs = []
        
        # Check if we need to add a serial primary key
        has_primary_key = any(col.get('primary_key', False) for col in column_definitions)
        
        if not has_primary_key:
            # Add an ID column as primary key
            column_strs.append(f'"{primary_key_column}" SERIAL PRIMARY KEY')
        
        for col in column_definitions:
            col_name = col.get('name')
            col_type = col.get('type', 'TEXT')
            nullable = col.get('nullable', True)
            default = col.get('default')
            primary_key = col.get('primary_key', False)
            
            if not col_name:
                continue
                
            # Build the column definition
            col_def = f'"{col_name}" {col_type}'
            
            if primary_key:
                col_def += " PRIMARY KEY"
                
            if not nullable:
                col_def += " NOT NULL"
                
            if default is not None:
                col_def += f" DEFAULT {default}"
                
            column_strs.append(col_def)
        
        # Create the SQL statement
        exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        columns_sql = ",\n    ".join(column_strs)
        
        create_table_sql = f"""
        CREATE TABLE {exists_clause}"{table_name}" (
        {columns_sql}
        )
        """
        
        # Execute the SQL based on engine type
        log.info(f"Creating table '{table_name}' with explicit column definitions")
        try:
            if self.engine_type == "pg8000":
                result = self._execute_sql_pg8000(create_table_sql)
            else:
                result = await self._execute_sql_async_langchain(create_table_sql)
                
            log.info(f"Table '{table_name}' created successfully")
            return result
        except Exception as e:
            log.error(f"Error creating table: {e}")
            raise

    def _get_sql_type_safe(self, value):
        """
        Enhanced version of _get_sql_type with better type detection.
        Handles placeholder values and common patterns.
        
        Args:
            value: The value to determine the column type
            
        Returns:
            str: SQL type
        """
        if value is None:
            return "TEXT"
        
        # Handle placeholder values
        if isinstance(value, str) and (value.startswith("No ") or value.lower() in ("none", "n/a", "null", "")):
            return "TEXT"  # Always use TEXT for placeholder values
        
        if isinstance(value, dict):
            return "JSONB"
        elif isinstance(value, list):
            return "JSONB"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "NUMERIC"
        else:
            # Check if it's a date string
            if isinstance(value, str):
                # Try to detect date formats
                value_lower = value.lower()
                if len(value) in (8, 10) and ('-' in value or '/' in value):
                    # Likely a date (YYYY-MM-DD or MM/DD/YYYY)
                    return "DATE"
                elif 'date' in value_lower or 'time' in value_lower:
                    # Column name hint suggests it's a date
                    return "TIMESTAMP"
                elif any(currency in value for currency in ('$', '€', '£')):
                    # Likely a monetary value
                    return "NUMERIC"
                
            # Default to TEXT
            return "TEXT"