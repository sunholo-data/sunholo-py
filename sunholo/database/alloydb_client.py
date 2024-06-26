try:
    import pg8000
    import sqlalchemy
    from sqlalchemy.exc import DatabaseError, ProgrammingError
    from google.cloud.alloydb.connector import Connector
except ImportError:
    AlloyDBEngine = None
    pass

from .database import get_vector_size
from ..logging import log

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
         - project_id (str): GCP project ID where the AlloyDB instance resides.
         - region (str): The region where the AlloyDB instance is located.
         - cluster_name (str): The name of the AlloyDB cluster.
         - instance_name (str): The name of the AlloyDB instance.
         - user (str): The database user name.
         - password (str): The database user's password.
         - db_name (str): The name of the database.
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