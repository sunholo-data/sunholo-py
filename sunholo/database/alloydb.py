import pg8000
import sqlalchemy
import os

from sqlalchemy.exc import DatabaseError, ProgrammingError
from asyncpg.exceptions import DuplicateTableError

from google.cloud.alloydb.connector import Connector
from langchain_google_alloydb_pg import AlloyDBEngine, Column, AlloyDBLoader, AlloyDBDocumentSaver
from google.cloud.alloydb.connector import IPTypes

from ..logging import log
from ..utils.config import load_config_key

def create_alloydb_engine(vector_name):

    alloydb_config = load_config_key(
        'alloydb_config', 
        vector_name=vector_name, 
        filename = "config/llm_config.yaml"
    )

    if alloydb_config is None:
        raise ValueError("No alloydb_config was found")

    ALLOYDB_DB = os.environ.get("ALLOYDB_DB")
    if ALLOYDB_DB is None:
        log.error(f"Could not locate ALLOYDB_DB environment variable for {vector_name}")
        raise ValueError("Could not locate ALLOYDB_DB environment variable")
    log.info(f"ALLOYDB_DB environment variable found for {vector_name} - {ALLOYDB_DB}")
    
    log.info("Inititaing AlloyDB Langchain")

    engine = AlloyDBEngine.from_instance(
        project_id=alloydb_config["project_id"],
        region=alloydb_config["region"],
        cluster=alloydb_config["cluster"],
        instance=alloydb_config["instance"],
        database=alloydb_config.get("database") or ALLOYDB_DB,
        ip_type=alloydb_config.get("ip_type") or IPTypes.PRIVATE
    )

    return engine

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
                 project_id: str, 
                 region: str, 
                 cluster_name:str, 
                 instance_name:str, 
                 user:str, 
                 password=None, 
                 db="postgres"):
        """Initializes the AlloyDB client.

        Args:
            project_id (str): GCP project ID where the AlloyDB instance resides.
            region (str): The region where the AlloyDB instance is located.
            cluster_name (str): The name of the AlloyDB cluster.
            instance_name (str): The name of the AlloyDB instance.
            user (str): The database user name.
            password (str): The database user's password.
            db_name (str): The name of the database.
        """
        self.connector = Connector()
        self.inst_uri = self._build_instance_uri(project_id, region, cluster_name, instance_name)
        self.engine = self._create_engine(self.inst_uri, user, password, db)

    def _build_instance_uri(self, project_id, region, cluster_name, instance_name):
        return f"projects/{project_id}/locations/{region}/clusters/{cluster_name}/instances/{instance_name}"

    def _create_engine(self, inst_uri, user, password, db):
        def getconn() -> pg8000.dbapi.Connection:
            conn = self.connector.connect(
                inst_uri,
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
            creator=getconn
        )
        engine.dialect.description_encoding = None
        log.info(f"Created AlloyDB engine for {inst_uri} and user: {user}")
        return engine

    def execute_sql(self, sql_statement):
        """Executes a given SQL statement with error handling.

        Args:
            sql_statement (str): The SQL statement to execute.

        Returns:
            The result of the execution, if any.
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

alloydb_table_cache = {}  # Our cache, initially empty  # noqa: F841
def create_alloydb_table(vector_name, engine, type = "vectorstore", alloydb_config=None, username=None):
    global alloydb_table_cache

    try:
        if type == "vectorstore":
            from .database import get_vector_size
            vector_size = get_vector_size(vector_name, config_file="config/llm_config.yaml")
            table_name = f"{vector_name}_{type}_{vector_size}"
            if table_name in alloydb_table_cache:
                log.info(f"AlloyDB Table '{table_name}' exists in cache, skipping creation.")

                return table_name
            log.info(f"# Creating AlloyDB table {table_name}")
            try:
                engine.init_vectorstore_table(
                    table_name,
                    vector_size=vector_size,
                    metadata_columns=[Column("source", "TEXT", nullable=True),
                                      Column("docstore_doc_id", nullable=True),
                                      Column("eventTime", "TIMESTAMPTZ", nullable=True)],
                    overwrite_existing=False
                )
            except Exception as err:
                log.info(f"Could not create the table, create it yourself - {str(err)}")
                alloydb_table_cache[table_name] = True 
                return table_name
            
            log.info(f"## Created AlloyDB Table: {table_name} with vector size: {vector_size}")
            alloydb_table_cache[table_name] = True 

            return table_name
        
        elif type == "docstore":
            table_name = f"{table_name}_docstore"
            if table_name in alloydb_table_cache:
                log.info(f"AlloyDB Table '{table_name}' exists, skipping creation.")

                return table_name
            
            create_docstore_table(table_name, alloydb_config=alloydb_config, username=username)
            alloydb_table_cache[table_name] = True 

            return table_name
        
        elif type == "chatstore":
            raise NotImplementedError("Chat history not implemented yet")
        else:
            raise ValueError("type was not one of vectorstore, docstore or chatstore")
    except DuplicateTableError: 
        log.info("AlloyDB Table already exists (DuplicateTableError) - caching name")
        alloydb_table_cache[table_name] = True 

        return table_name
    
    except ProgrammingError as err:
        if "already exists" in str(err):
            log.info("AlloyDB Table already exists (ProgrammingError) - caching name")
            alloydb_table_cache[table_name] = True

            return table_name
    
def create_vectorstore_table(table_name, alloydb_config, username):
    ALLOYDB_DB = os.environ.get("ALLOYDB_DB")
    if ALLOYDB_DB is None:
        log.error(f"Could not locate ALLOYDB_DB environment variable for {table_name}")
        raise ValueError("Could not locate ALLOYDB_DB environment variable")
    
    sql = """
CREATE TABLE IF NOT EXISTS {table_name} (
            "langchain_id" UUID PRIMARY KEY,
            "content" TEXT NOT NULL,
            "embedding" vector(1536) NOT NULL,
"source" TEXT ,
"langchain_metadata" JSON
);
"""
    ALLOYDB_DB = os.environ.get("ALLOYDB_DB")
    if ALLOYDB_DB is None:
        log.error(f"Could not locate ALLOYDB_DB environment variable for {table_name}")
        raise ValueError("Could not locate ALLOYDB_DB environment variable")
        
    client = AlloyDBClient(
        project_id=alloydb_config["project_id"],
        region=alloydb_config["region"],
        cluster_name=alloydb_config["cluster"],
        instance_name=alloydb_config["instance"],
        db=alloydb_config.get("database") or ALLOYDB_DB,
        user=username
    )

    client.execute_sql(sql)

    return table_name

def create_docstore_table(table_name, alloydb_config, username):
    ALLOYDB_DB = os.environ.get("ALLOYDB_DB")
    if ALLOYDB_DB is None:
        log.error(f"Could not locate ALLOYDB_DB environment variable for {table_name}")
        raise ValueError("Could not locate ALLOYDB_DB environment variable")
        
    client = AlloyDBClient(
        project_id=alloydb_config["project_id"],
        region=alloydb_config["region"],
        cluster_name=alloydb_config["cluster"],
        instance_name=alloydb_config["instance"],
        db=alloydb_config.get("database") or ALLOYDB_DB,
        user=username
    )

    # Execute other SQL statements
    client.execute_sql(f"CREATE TABLE {table_name} (page_content TEXT, doc_id TEXT, source TEXT, langchain_metadata JSONB)")

    return table_name

def add_document_if_not_exists(doc, vector_name):
    table_name = f"{vector_name}_docstore"
    doc_id = doc.metadata.get("doc_id")
    if not doc_id:
        raise ValueError(f"No doc_id found for document: {doc.metadata}")

    check_query = f"""
        SELECT * 
        FROM {table_name}
        WHERE doc_id = {doc_id}
        LIMIT 1
    """
    #TODO add check for timeperiod etc.

    docs = load_alloydb_sql(check_query, vector_name)
    if docs:
        log.info(f"Found existing document with same doc_id - {doc_id}, skipping import")
        return doc_id

    engine = create_alloydb_engine(vector_name)

    saver = AlloyDBDocumentSaver.create_sync(
        engine=engine,
        table_name=table_name,
        metadata_columns=["source", "doc_id", "images_gsurls", "chunk_metadata"]
    )
    saver.add_documents([doc])
    source = doc.metadata.get("source")
    doc_id = doc.metadata.get("doc_id")
    log.info(f"Saved {doc_id} - {source} to alloydb docstore: {table_name}")

    return doc_id

def load_alloydb_sql(sql, vector_name):
    engine = create_alloydb_engine(vector_name=vector_name)
    log.info(f"Alloydb doc query: {sql}")

    loader = AlloyDBLoader.create_sync(
            engine=engine,
            query=sql)
    
    documents = loader.load()
    log.info(f"Loaded {len(documents)} from the database.")
    return documents

async def load_alloydb_sql_async(sql, vector_name):
    engine = create_alloydb_engine(vector_name=vector_name)    
    log.info(f"Alloydb doc query: {sql}")

    loader = await AlloyDBLoader.create(
            engine=engine,
            query=sql)
    
    documents = await loader.aload()
    log.info(f"Loaded {len(documents)} from the database.")
    return documents

async def get_sources_from_docstore_async(sources, vector_name):
    
    if not sources:
        log.warning("No sources found for alloydb fetch")

    table_name = f"{vector_name}_docstore"

    like_patterns = ', '.join(f"'%{source}%'" for source in sources)  
    if not like_patterns:
        log.warning("Alloydb doc query found no like_patterns")
        return []
    
    query = f"""
        SELECT * 
        FROM {table_name}
        WHERE TRIM(source) ILIKE ANY (ARRAY[{like_patterns}])
        ORDER BY source ASC
        LIMIT 500
    """
    documents = await load_alloydb_sql_async(query, vector_name)
    
    return documents