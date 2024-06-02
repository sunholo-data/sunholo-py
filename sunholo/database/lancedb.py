from ..logging import log

def create_lancedb_index(bucket, vector_name, num_partitions=256, num_sub_vectors=96, text_key="text"):
    try:
        import lancedb
        #import tantivy
    except ImportError:
        raise ValueError("Could not import lancedb module, install via `pip install sunholo[database]`")
        
    try:
        db = lancedb.connect(bucket) 
        tbl = db.open_table(vector_name)

        tbl.create_index(num_partitions=num_partitions, num_sub_vectors=num_sub_vectors)
        tbl.create_fts_index(text_key)
        log.info(f'Index creation for {vector_name} success')
    except Exception as e: 
        log.info(f'Index creation for {vector_name} failed: {e}')
    
    
