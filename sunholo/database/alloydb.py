import pg8000
import sqlalchemy
from sqlalchemy.exc import ProgrammingError
from google.cloud.alloydb.connector import Connector

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

    def __init__(self, project_id, region, cluster_name, instance_name, user, password=None, db="postgres"):
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
        with self.engine.connect() as conn:
            try:
                logging.info(f"Executing SQL statement: {sql_}")
                result = conn.execute(sql_)
                return result  
            except ProgrammingError as e:
                if "already exists" in str(e):
                    logging.warning(f"Error ignored: {str(e)}. Assuming object already exists.")
                else:
                    raise  
