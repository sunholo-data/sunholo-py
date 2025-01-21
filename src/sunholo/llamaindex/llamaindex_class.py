import os
import tempfile

try:
    from vertexai.preview import rag
    from google.cloud.aiplatform_v1beta1 import RetrieveContextsResponse
except ImportError:
    rag = None

from ..utils import ConfigManager
from ..custom_logging import log

try:
    from ..cli.sun_rich import console
except ImportError:
    console = None

class LlamaIndexVertexCorpusManager:
    """
    A manager class for handling RAG corpora operations with Vertex AI.

    Attributes:
        config (ConfigManager): Configuration manager for fetching project settings.
        project_id (str): GCP project ID.
        location (str): GCP location.
    """

    def __init__(self, config: ConfigManager = None, project_id: str = None, location: str = None):
        """
        Initializes the LlamaIndexVertexCorpusManager.

        Args:
            config (ConfigManager): Configuration manager for fetching project settings.
            project_id (str): GCP project ID.
            location (str): GCP location.

        Raises:
            ImportError: If vertexai is not installed.
        """
        from ..vertex.init import init_vertex

        if rag is None:
            raise ImportError("You must install vertexai via `pip install sunholo[gcp]`")
        
        self.config = config
        self.project_id = project_id
        self.location = location
        self.corpus_display_name = ""
        self.corpus = ""

        if config:
            self.project_id = self.config.vacConfig('project_id') or project_id
            self.location = self.config.vacConfig('location') or location

        init_vertex(location=self.location, project_id=self.project_id)

    def upload_text(self, text: str, corpus_display_name: str, description: str = None):
        """
        Uploads a text string to a specified corpus by saving it to a temporary file first.

        Args:
            text (str): The text content to upload.
            corpus_display_name (str): The display name of the corpus.
            description (str, optional): Description of the text upload.

        Returns:
            The uploaded file object.
        """
        # Create a temporary file and write the text to it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(text.encode('utf-8'))
            temp_filename = temp_file.name
        
        try:
            # Upload the temporary file
            log.info(f"Uploading text:{text[:50]}... to {corpus_display_name}")
            uploaded_file = self.upload_file(temp_filename, corpus_display_name, description or text[:50])
        finally:
            # Clean up the temporary file
            os.remove(temp_filename)
        
        log.info(f"Successfully uploaded text:{text[:50]}... to {corpus_display_name}")

        return uploaded_file
    
    def upload_file(self, filename:str, corpus_display_name:str, description:str=None):
        corpus = self.find_corpus_from_list(corpus_display_name)

        rag_file = rag.upload_file(
            corpus_name=corpus.name,
            path=filename,
            display_name=filename,
            description=description or f"Upload for {filename}",
        )
        log.info(f"Uploaded file: {rag_file}")

        return rag_file
    
    def import_files(self, file_imports:list[str], corpus_display_name:str):
        corpus = self.find_corpus_from_list(corpus_display_name)

        log.info(f"Importing files: {file_imports} into {corpus.name}")
        response = rag.import_files(
            corpus_name=corpus.name,
            paths=file_imports,
            chunk_size=512,  # Optional
            chunk_overlap=100,  # Optional
            max_embedding_requests_per_min=900,  # Optional
        )
        log.info(f"Imported files: {response}")

        return response
    
    def list_files(self, corpus_display_name:str):
        corpus = self.find_corpus_from_list(corpus_display_name)
        files = rag.list_files(corpus_name=corpus.name)

        log.info(f"--Files in {corpus.name}:\n{files}")
        
        return files

    def find_file_from_list(self, display_name: str, corpus_display_name:str):
        """
        Finds a file from the list of files by its display name.

        Args:
            display_name (str): The display name of the file.
            corpus_display_name (str): The display name of the corpus to look within

        Returns:
            The found file object if it exists, otherwise None.
        """
        files = self.list_files(corpus_display_name)
        for file in files:
            if display_name == file.display_name:
                log.info(f"Found existing file with display name: {display_name}")

                return file
        
        return None
    
    def get_file(self, file_display_name:str=None, file_name:str=None, corpus_display_name:str=None):
        
        if file_display_name:
            rag_file = self.find_file_from_list(file_display_name, corpus_display_name)
            log.info(f"Found {rag_file} via display name: {file_display_name}")
            
            return rag_file
        
        if not file_name:
            raise ValueError("Need to supply one of file_display_name or file_name")

        corpus = self.find_corpus_from_list(corpus_display_name)
        if file_name.startswith("projects/"):
            rag_file = rag.get_file(name=file_name)
        else:
            if not corpus_display_name:
                raise ValueError("Must supply corpus_display_name if not a full file_name")
            rag_file = rag.get_file(name=file_name, corpus_name=corpus.name)
        
        log.info(f"Found {rag_file}")

        return rag_file
    
    def delete_file(self, file_name, corpus_display_name:str):

        corpus = self.find_corpus_from_list(corpus_display_name)
        if file_name.startswith("projects/"):
            rag.delete_file(name=file_name)
        else:
            if not corpus_display_name:
                raise ValueError("Must supply corpus_display_name if not a full file_name")
            rag.delete_file(name=file_name, corpus_name=corpus.name)
        
        log.info(f"File {file_name} deleted.")

        return True
    
    def query_corpus(self, query:str, corpus_disply_name:str):
        corpus = self.find_corpus_from_list(corpus_disply_name)

        log.info(f"Querying {corpus.name=} with {query=}")
        
        response:RetrieveContextsResponse = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=corpus.name,
                    # Supply IDs from `rag.list_files()`.
                    # rag_file_ids=["rag-file-1", "rag-file-2", ...],
                )
            ],
            text=query,
            similarity_top_k=10,  # Optional
            vector_distance_threshold=0.5,  # Optional
        )

        return response

    def list_corpora(self):
        """
        List all VertexAI Corpus for the project/location
        """
        try:
            return rag.list_corpora()
        except Exception as err:
            log.error(f"Could not list corpora: {str(err)}")
            return []

    
    def find_corpus_from_list(self, display_name: str):
        """
        Finds a corpus from the list of corpora by its display name.

        Args:
            display_name (str): The display name of the corpus.

        Returns:
            The found corpus object if it exists, otherwise None.
        """
        if display_name == self.corpus_display_name:
            return self.corpus
        corpora = self.list_corpora()
        for corp in corpora:
            if display_name == corp.display_name:
                log.info(f"Found existing corpus with display name: {display_name}")
                self.corpus = corp
                return corp
        return None

    def create_corpus(self, display_name: str, description: str = None):
        """
        Creates a new corpus or returns an existing one with the specified display name.

        Args:
            display_name (str): The display name of the corpus.
            description (str, optional): Description of the corpus.

        Returns:
            The created or found corpus object.
        """
        corp = self.find_corpus_from_list(display_name)
        if corp:
            return corp
        
        corpus = rag.create_corpus(display_name=display_name, description=description or f"Corpus for {display_name}")
        log.info(f"created Llamaindex corpus {corpus}")

        return corpus

    def delete_corpus(self, display_name: str):
        """
        Deletes a corpus by its display name.

        Args:
            display_name (str): The display name of the corpus.

        Returns:
            bool: True if the corpus was deleted, False otherwise.
        """
        corp = self.find_corpus_from_list(display_name)
        if corp:
            rag_id = corp.name
            rag.delete_corpus(name=rag_id)
            log.info(f"Deleted {rag_id}")
            return True
        
        log.warning(f"Could not find a corp to delete with name {display_name}")
        return False

    def fetch_corpus(self, display_name: str):
        """
        Fetches a corpus by its display name.

        Args:
            display_name (str): The display name of the corpus.

        Returns:
            The fetched corpus object.

        Raises:
            ValueError: If the corpus with the specified display name does not exist.
        """
        corp = self.find_corpus_from_list(display_name)
        if not corp:
            raise ValueError(f"Could not find any corpus with display_name: {display_name}")
        return rag.get_corpus(name=corp.name)

def llamaindex_command(args):
    if console is None:
        raise ImportError("Need cli tools to use `sunholo llamaindex` - install via `pip install sunholo[cli]`")
    
    config = ConfigManager(args.vac)
    manager = LlamaIndexVertexCorpusManager(config=config)
    
    if args.action == "create":
        manager.create_corpus(display_name=args.display_name, description=args.description)
    elif args.action == "delete":
        manager.delete_corpus(display_name=args.display_name)
    elif args.action == "fetch":
        corpus = manager.fetch_corpus(display_name=args.display_name)
        console.print(corpus)
    elif args.action == "find":
        corpus = manager.find_corpus_from_list(display_name=args.display_name)
        console.print(corpus)
    elif args.action == "list":
        corpora = manager.list_corpora()
        console.print(corpora)
    elif args.action == "import_files":
        manager.import_files(file_imports=args.file_imports, corpus_display_name=args.display_name)
    elif args.action == "upload_file":
        manager.upload_file(filename=args.filename, corpus_display_name=args.display_name, description=args.description)
    elif args.action == "upload_text":
        manager.upload_text(text=args.text, corpus_display_name=args.display_name, description=args.description)
    elif args.action == "list_files":
        files = manager.list_files(corpus_display_name=args.display_name)
        if files:
            console.print(files)
        else:
            console.print("No files found for {args.display_name}")
    elif args.action == "get_file":
        file = manager.get_file(file_display_name=args.file_name, corpus_display_name=args.display_name)
        console.print(file)
        return file
    elif args.action == "delete_file":
        deleted = manager.delete_file(args.file_name, corpus_display_name=args.display_name)
        if deleted:
            console.print(f"Deleted {args.file_name}")
        else:
            console.print(f"ERROR: Could not delete {args.file_name}")

    elif args.action == "query":
        answer = manager.query_corpus(args.query, corpus_disply_name=args.display_name)
        if answer:
            console.print(answer)
        else:
            console.print(f"No answer found for {args.query} in {args.display_name}")
    else:
        console.print(f"Unknown action: {args.action}")

def setup_llamaindex_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'llamaindex' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    # LlamaIndex subparser setup
    llamaindex_parser = subparsers.add_parser('llamaindex', help='Manage LlamaIndex corpora')
    llamaindex_subparsers = llamaindex_parser.add_subparsers(dest='action', help='LlamaIndex subcommands')

    # LlamaIndex create command
    create_parser = llamaindex_subparsers.add_parser('create', help='Create a new corpus')
    create_parser.add_argument('display_name', help='The name of the corpus')
    create_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')
    create_parser.add_argument('--description', help='Description of the corpus', default=None)

    # LlamaIndex delete command
    delete_parser = llamaindex_subparsers.add_parser('delete', help='Delete a corpus')
    delete_parser.add_argument('display_name', help='The name of the corpus')
    delete_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex fetch command
    fetch_parser = llamaindex_subparsers.add_parser('fetch', help='Fetch a corpus')
    fetch_parser.add_argument('display_name', help='The name of the corpus')
    fetch_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex find command
    find_parser = llamaindex_subparsers.add_parser('find', help='Find a corpus')
    find_parser.add_argument('display_name', help='The name of the corpus')
    find_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex list command
    list_parser = llamaindex_subparsers.add_parser('list', help='List all corpus')
    list_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex import_files command
    import_files_parser = llamaindex_subparsers.add_parser('import_files', help='Import files from URLs to a corpus')
    import_files_parser.add_argument('display_name', help='The name of the corpus')
    import_files_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')
    import_files_parser.add_argument('file_imports', nargs='+', help='The list of file URLs to import')

    # LlamaIndex upload_file command
    upload_file_parser = llamaindex_subparsers.add_parser('upload_file', help='Upload a local file to a corpus')
    upload_file_parser.add_argument('display_name', help='The name of the corpus')
    upload_file_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')
    upload_file_parser.add_argument('filename', help='The local file path to upload')
    upload_file_parser.add_argument('--description', help='Description of the file upload', default=None)

    # LlamaIndex upload_text command
    upload_text_parser = llamaindex_subparsers.add_parser('upload_text', help='Upload text to a corpus')
    upload_text_parser.add_argument('display_name', help='The name of the corpus')
    upload_text_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')
    upload_text_parser.add_argument('text', help='The text content to upload')
    upload_text_parser.add_argument('--description', help='Description of the text upload', default=None)

    # LlamaIndex list_files command
    list_files_parser = llamaindex_subparsers.add_parser('list_files', help='List all files in a corpus')
    list_files_parser.add_argument('display_name', help='The name of the corpus')
    list_files_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex get_file command
    get_file_parser = llamaindex_subparsers.add_parser('get_file', help='Get a file from a corpus')
    get_file_parser.add_argument('display_name', help='The name of the corpus')
    get_file_parser.add_argument('file_name', help='The name of the file to get')
    get_file_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex delete_file command
    delete_file_parser = llamaindex_subparsers.add_parser('delete_file', help='Delete a file from a corpus')
    delete_file_parser.add_argument('display_name', help='The name of the corpus')
    delete_file_parser.add_argument('file_name', help='The name of the file to delete')
    delete_file_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    # LlamaIndex query command
    query_parser = llamaindex_subparsers.add_parser('query', help='Query a corpus')
    query_parser.add_argument('display_name', help='The name of the corpus')
    query_parser.add_argument('query', help='The query string')
    query_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    llamaindex_parser.set_defaults(func=llamaindex_command)

    # If no subcommand is provided, print the help message
    llamaindex_parser.set_defaults(func=lambda args: llamaindex_parser.print_help() if args.action is None else llamaindex_command)
