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
import time
import math

from ..utils.config import get_module_filepath
from ..logging import log
from ..utils.config import load_config_key



def setup_supabase(vector_name:str, verbose:bool=False):
    hello = f"Setting up supabase database: {vector_name}"
    log.debug(hello)
    if verbose:
        print(hello)
    setup_database("supabase", vector_name, verbose)

def setup_cloudsql(vector_name:str, verbose:bool=False):
    hello = f"Setting up cloudsql database: {vector_name}"
    log.debug(hello)
    if verbose:
        print(hello)
    setup_database(vector_name, verbose)

def lookup_connection_env(vs_str):
    
    if vs_str == "supabase":
        return "DB_CONNECTION_STRING"
    elif vs_str == "cloudsql":
        return "PGVECTOR_CONNECTION_STRING"
    elif vs_str == "alloydb":
        return "ALLOYDB_CONNECTION_STRING"
    
    raise ValueError("Could not find vectorstore for {vs_str}")


def get_vector_size(vector_name: str):

    llm_str = None
    embed_dict = load_config_key("embedder", vector_name, kind="vacConfig")

    if embed_dict:
        llm_str = embed_dict.get('llm')

    if llm_str is None:
        llm_str = load_config_key("llm", vector_name, kind="vacConfig")

    if not isinstance(llm_str, str):
        raise ValueError(f"get_vector_size() did not return a value string for {vector_name} - got {llm_str} instead")
    
    vector_size = 768
    if llm_str == 'openai':
        vector_size = 1536 # openai

    log.debug(f'vector size: {vector_size}')
    
    return vector_size

def setup_database(type, vector_name:str, verbose:bool=False):

    connection_env = lookup_connection_env(type)
    
    params = {'vector_name': vector_name, 'vector_size': get_vector_size(vector_name)}

    execute_sql_from_file("database/sql/sb/setup.sql", params, verbose=verbose, connection_env=connection_env)
    execute_sql_from_file("database/sql/sb/create_table.sql", params, verbose=verbose, connection_env=connection_env)
    execute_sql_from_file("database/sql/sb/create_function.sql", params, verbose=verbose, connection_env=connection_env)

    if verbose: 
        print("Ran all setup SQL statements")
    
    return True

def return_sources_last24(vector_name:str):
    params = {'vector_name': vector_name, 'time_period':'1 day'}
    return execute_sql_from_file("sql/sb/return_sources.sql", params, return_rows=True, 
                                 connection_env=lookup_connection_env(vector_name))

def delete_row_from_source(source: str, vector_name:str):
    # adapt the user input and decode from bytes to string to protect against sql injection
    try:
        import psycopg2
        from psycopg2.extensions import adapt
    except ImportError:
        log.error("Couldn't import psycopg2 - please install via 'pip install psycopg2'") 

    source = adapt(source).getquoted().decode()
    sql_params = {'source_delete': source}
    sql = f"""
        DELETE FROM {vector_name}
        WHERE metadata->>'source' = %(source_delete)s
    """

    do_sql(sql, sql_params=sql_params, connection_env=lookup_connection_env(vector_name))



def do_sql(sql, sql_params=None, return_rows=False, verbose=False, connection_env='DB_CONNECTION_STRING', max_retries=5):

    if connection_env is None:
        raise ValueError("Need to specify connection_env to connect to DB")
    
    try:
        import psycopg2
        from psycopg2.extensions import adapt
    except ImportError:
        log.error("Couldn't import psycopg2 - please install via 'pip install psycopg2'") 

    rows = []
    connection_string = os.getenv(connection_env, None)
    if connection_string is None:
        raise ValueError("No connection string")

    for attempt in range(max_retries):
        try:
            connection = psycopg2.connect(connection_string)
            cursor = connection.cursor()

            if verbose:
                log.info(f"SQL: {sql}")
            else:
                pass
            # execute the SQL - raise the error if already found
            cursor.execute(sql, sql_params)

            # commit the transaction to save changes to the database
            connection.commit()

            if return_rows:
                rows = cursor.fetchall()
            log.debug("SQL successfully fetched")
            break  # If all operations were successful, break the loop

        except (psycopg2.errors.DuplicateObject, 
                psycopg2.errors.DuplicateTable, 
                psycopg2.errors.DuplicateFunction) as e:
            log.debug(str(e))
            if verbose:
                print(str(e))
            continue

        except psycopg2.errors.InternalError as error:
            log.error(f"InternalError, retrying... Attempt {attempt+1} out of {max_retries}")
            time.sleep(math.pow(2, attempt))  # Exponential backoff
            continue  # Go to the next iteration of the loop to retry the operation

        except (Exception, psycopg2.Error) as error:
            log.error(f"Error while connecting to PostgreSQL: {str(error)}", exc_info=True)
            continue

        finally:
            if connection:
                cursor.close()
                connection.close()
                log.debug("PostgreSQL connection is closed")
    
        # If we've exhausted all retries and still haven't succeeded, raise an error
        if attempt + 1 == max_retries:
            raise Exception("Maximum number of retries exceeded")

    if rows:
        return rows
    
    return None


def execute_sql_from_file(filepath, params, return_rows=False, verbose=False, connection_env=None):
    
    filepath = get_module_filepath(filepath)
    log.info(f"Executing SQL from file {filepath}")

    # read the SQL file
    with open(filepath, 'r') as file:
        sql = file.read()

    # substitute placeholders in the SQL
    sql = sql.format(**params)
    rows = do_sql(sql, return_rows=return_rows, verbose=verbose, connection_env=connection_env)
    
    if return_rows:
        if rows is None: return None
        return rows
    
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Setup a database",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("vectorname", help="The namespace for vectorstore")
    parser.add_argument("connection_env", help="The connection environment string", default="DB_CONNECTION_STRING")

    args = parser.parse_args()
    config = vars(args)

    vector_name = config.get('vectorname', None)
    if vector_name is None:
        raise ValueError("Must provide a vectorname")
    
    setup_database(vector_name, verbose=True, connection_env=config.get("connection_env"))

