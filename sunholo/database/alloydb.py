import os
try:
    from sqlalchemy.exc import DatabaseError, ProgrammingError
    from asyncpg.exceptions import DuplicateTableError
    from langchain_google_alloydb_pg import AlloyDBEngine, Column, AlloyDBLoader, AlloyDBDocumentSaver
    from google.cloud.alloydb.connector import IPTypes
except ImportError:
    AlloyDBEngine = None
    pass

from .database import get_vector_size
from .alloydb_client import AlloyDBClient

from ..logging import log
from ..utils.config import load_config_key


def create_alloydb_engine(vector_name):

    if not AlloyDBEngine:
        log.error("Can't create AlloyDBEngine - install via `pip install sunholo[gcp,database]`")
        raise ValueError("Can't import AlloyDBEngine")

    alloydb_config = load_config_key(
        'alloydb_config', 
        vector_name=vector_name, 
        kind="vacConfig"
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

alloydb_table_cache = {}  # Our cache, initially empty  # noqa: F841
def create_alloydb_table(vector_name, engine, type = "vectorstore", alloydb_config=None, username=None):
    global alloydb_table_cache

    try:
        if type == "vectorstore":
            from .database import get_vector_size
            vector_size = get_vector_size(vector_name)
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
                                      Column("docstore_doc_id", "UUID", nullable=True),
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
    if not doc:
        log.warning("Got None type for document")
        return None
    
    doc_id = doc.metadata.get("doc_id")
    if not doc_id:
        raise ValueError(f"No doc_id found for document: {doc.metadata}")

    check_query = f"""
        SELECT * 
        FROM {table_name}
        WHERE doc_id = '{doc_id}'
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
    log.info(f"Alloydb (sync) doc query: {sql}")

    loader = AlloyDBLoader.create_sync(
            engine=engine,
            query=sql)
    
    documents = loader.load()
    log.info(f"Loaded {len(documents)} from the database.")

    return documents

_alloydb_loader = None

async def load_alloydb_sql_async(sql, vector_name):
    global _alloydb_loader
    if _alloydb_loader is None:
        engine = create_alloydb_engine(vector_name=vector_name)
        _alloydb_loader = await AlloyDBLoader.create(engine=engine, query=sql)
    else:
        _alloydb_loader.query = sql  # Update the query if the loader is reused

    log.info(f"Alloydb (async) doc query: {sql}")
    documents = await _alloydb_loader.aload()
    log.info(f"Loaded {len(documents)} from the database.")
    
    return documents

def and_or_ilike(sources, search_type="OR", operator="ILIKE"):
    unique_sources = set(sources)
    # Choose the delimiter based on the search_type argument
    delimiter = ' AND ' if search_type.upper() == "AND" else ' OR '

    # Build the conditional expressions based on the chosen delimiter
    conditions = delimiter.join(f"TRIM(source) {operator} '%{source}%'" for source in unique_sources)
    if not conditions:
        log.warning("Alloydb doc query found no like_patterns")
        return []
    
    return conditions

def _get_sources_from_docstore(sources, vector_name, search_type="OR"):
    if not sources:
        log.warning("No sources found for alloydb fetch")
        return []

    table_name = f"{vector_name}_docstore"

    conditions = and_or_ilike(sources, search_type=search_type)
    
    query = f"""
        SELECT * 
        FROM {table_name}
        WHERE {conditions}
        ORDER BY langchain_metadata->>'objectId' ASC
        LIMIT 500;
    """

    return query


async def get_sources_from_docstore_async(sources, vector_name, search_type="OR"):
    
    query = _get_sources_from_docstore(sources, vector_name=vector_name, search_type=search_type)
    if not query:
        return []
    
    documents = await load_alloydb_sql_async(query, vector_name)
    
    return documents

def get_sources_from_docstore(sources, vector_name, search_type="OR"):
    
    query = _get_sources_from_docstore(sources, vector_name=vector_name, search_type=search_type)
    if not query:
        return []
    
    documents = load_alloydb_sql(query, vector_name)
    
    return documents

def delete_sources_from_alloydb(sources, vector_name):
    """
    Deletes from both vectorstore and docstore
    """

    vector_length = get_vector_size(vector_name)

    conditions = and_or_ilike(sources, operator="=")

    if not conditions:
        log.warning("No conditions were specified, not deleting whole table!")
        return False

    query = f"""
        DELETE FROM {vector_name}_docstore
        WHERE {conditions};
        DELETE FROM {vector_name}_vectorstore_{vector_length}
        WHERE {conditions}
    """
