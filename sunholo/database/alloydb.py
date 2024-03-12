import pg8000
import sqlalchemy
from sqlalchemy.exc import DatabaseError
from google.cloud.alloydb.connector import Connector

from langchain_google_alloydb_pg import AlloyDBEngine, AlloyDBVectorStore, Column
from google.cloud.alloydb.connector import IPTypes
from sqlalchemy.exc import ProgrammingError

from ..logging import setup_logging

logging = setup_logging()

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
        logging.info(f"Created AlloyDB engine for {inst_uri} and user: {user}")
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
                logging.info(f"Executing SQL statement: {sql_}")
                result = conn.execute(sql_)
            except DatabaseError as e:
                if "already exists" in str(e):
                    logging.warning(f"Error ignored: {str(e)}. Assuming object already exists.")
                else:
                    raise  
            finally:
                conn.close()

        return result  

alloydb_table_cache = {}  # Our cache, initially empty  # noqa: F841
def create_alloydb_table(table_name, engine):
    global alloydb_table_cache

    if table_name in alloydb_table_cache:
            logging.info(f"AlloyDB Table '{table_name}' exists, skipping creation.")
            return
    try:
        from .database import get_vector_size
        vector_size = get_vector_size(table_name, config_file="config/llm_config.yaml")
        engine.init_vectorstore_table(
            table_name,
            vector_size=vector_size,
            #metadata_columns=[Column("source", "VARCHAR", nullable=True),
            #                  Column("eventTime", "TIMESTAMPTZ", nullable=True)],
            metadata_columns=[Column("source", "TEXT", nullable=True)],
            overwrite_existing=False
        )
        logging.info(f"## Created AlloyDB Table: {table_name} with vector size: {vector_size}")
    except ProgrammingError as err:
        if "already exists" in str(err):
            logging.info(f"AlloyDB Table already exists - caching name: {str(err)}")
            alloydb_table_cache[table_name] = True 
