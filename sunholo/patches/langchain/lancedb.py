# from https://github.com/langchain-ai/langchain/blob/6c18f73ca56bb72cb964aaa668c3f8ac14237619/libs/community/langchain_community/vectorstores/lancedb.py
from __future__ import annotations

import uuid, time
from typing import Any, Iterable, List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore


class LanceDB(VectorStore):
    """`LanceDB` vector store.

    To use, you should have ``lancedb`` python package installed.

    Example:
        .. code-block:: python

            db = lancedb.connect('./lancedb')
            table = db.open_table('my_table')
            vectorstore = LanceDB(table, embedding_function)
            vectorstore.add_texts(['text1', 'text2'])
            result = vectorstore.similarity_search('text1')
    """

    def __init__(
        self,
        connection: Optional[Any] = None,
        embedding: Optional[Embeddings] = None,
        vector_key: Optional[str] = "vector",
        id_key: Optional[str] = "id",
        text_key: Optional[str] = "text",
        table_name: Optional[str] = "vectorstore",
    ):
        """Initialize with Lance DB connection"""
        try:
            import lancedb
        except ImportError:
            raise ImportError(
                "Could not import lancedb python package. "
                "Please install it with `pip install lancedb`."
            )
        if not isinstance(connection, lancedb.db.LanceTable):
            raise ValueError(
                "connection should be an instance of lancedb.db.LanceTable, ",
                f"got {type(connection)}",
            )
        self.lancedb = lancedb
        self._embedding = embedding
        self._vector_key = vector_key
        self._id_key = id_key
        self._text_key = text_key
        self._table_name = table_name

        if self._embedding is None:
            raise ValueError("embedding should be provided")

        if connection is not None:
            if not isinstance(connection, lancedb.db.LanceTable):
                raise ValueError(
                    "connection should be an instance of lancedb.db.LanceTable, ",
                    f"got {type(connection)}",
                )
            self._connection = connection
        else:
            self._connection = self._init_table()

    @property
    def embeddings(self) -> Embeddings:
        return self._embedding

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Turn texts into embedding and add it to the database

        Args:
            texts: Iterable of strings to add to the vectorstore.
            metadatas: Optional list of metadatas associated with the texts.
            ids: Optional list of ids to associate with the texts.

        Returns:
            List of ids of the added texts.
        """
        # Embed texts and create documents
        docs = []
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        embeddings = self._embedding.embed_documents(list(texts))
        for idx, text in enumerate(texts):
            embedding = embeddings[idx]
            metadata = metadatas[idx] if metadatas else {}
            docs.append(
                {
                    self._vector_key: embedding,
                    self._id_key: ids[idx],
                    self._text_key: text,
                    **metadata,
                }
            )

        max_retries = 5  
        retry_delay = 1 
        for attempt in range(max_retries):
            try:
                self._connection.add(docs)
                return ids  # If success, return immediately
            except OSError as e:
                if "429 Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        raise  # Re-raise the exception if max retries are reached
                else:
                    raise  # Re-raise the exception if it's not a rate limit error

        return ids

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> List[Document]:
        """Return documents most similar to the query

        Args:
            query: String to query the vectorstore with.
            k: Number of documents to return.

        Returns:
            List of documents most similar to the query.
        """
        query_type = kwargs.get('query_type', None)
        where_clause = kwargs.get('where', None)

        if query_type == "hybrid":
            # Hybrid search logic
            search_query = self._connection.search(query, query_type="hybrid")
        else:
            # Original search logic
            embedding = self._embedding.embed_query(query)
            search_query = self._connection.search(embedding, vector_column_name=self._vector_key)

        if where_clause:
            # Apply the where condition if specified
            search_query = search_query.where(where_clause)        

        docs = search_query.limit(k).to_arrow()
        
        columns = docs.schema.names
        return [
            Document(
                page_content=docs[self._text_key][idx].as_py(),
                metadata={
                    col: docs[col][idx].as_py()
                    for col in columns
                    if col != self._text_key
                },
            )
            for idx in range(len(docs))
        ]


    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        connection: Any = None,
        vector_key: Optional[str] = "vector",
        id_key: Optional[str] = "id",
        text_key: Optional[str] = "text",
        **kwargs: Any,
    ) -> LanceDB:
        instance = LanceDB(
            connection,
            embedding,
            vector_key,
            id_key,
            text_key,
        )
        instance.add_texts(texts, metadatas=metadatas, **kwargs)

        return instance

    def _init_table(self) -> Any:
        import pyarrow as pa

        schema = pa.schema(
            [
                pa.field(
                    self._vector_key,
                    pa.list_(
                        pa.float32(),
                        len(self.embeddings.embed_query("test")),  # type: ignore
                    ),
                ),
                pa.field(self._id_key, pa.string()),
                pa.field(self._text_key, pa.string()),
            ]
        )
        db = self.lancedb.connect("/tmp/lancedb")
        tbl = db.create_table(self._table_name, schema=schema, mode="overwrite")
        return tbl
    