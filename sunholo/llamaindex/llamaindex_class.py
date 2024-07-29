try:
    from vertexai.preview import rag
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

        if config:
            self.project_id = self.config.vacConfig('project_id') or project_id
            self.location = self.config.vacConfig('location') or location

        init_vertex(location=self.location, project_id=self.project_id)
    
    def list_corpora(self):
        """
        List all VertexAI Corpus for the project/location
        """
        return rag.list_corpora()
    
    def find_corpus_from_list(self, display_name: str):
        """
        Finds a corpus from the list of corpora by its display name.

        Args:
            display_name (str): The display name of the corpus.

        Returns:
            The found corpus object if it exists, otherwise None.
        """
        corpora = self.list_corpora()
        for corp in corpora:
            if display_name == corp.display_name:
                log.info(f"Found existing corpus with display name: {display_name}")
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
        corpura = manager.list_corpora()
        console.print(corpura)
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
    find_parser = llamaindex_subparsers.add_parser('list', help='List all corpus')
    find_parser.add_argument('vac', nargs='?', default="global", help='The VAC config to set it up for')

    llamaindex_parser.set_defaults(func=llamaindex_command)
