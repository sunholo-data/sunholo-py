import json
import uuid
import base64
from datetime import datetime, timezone
from argparse import Namespace
from pathlib import Path

from .sun_rich import console
from rich.progress import Progress

from ..invoke import invoke_vac
from .chat_vac import resolve_service_url
from .run_proxy import stop_proxy

def create_metadata(vac, metadata):
    now_utc = datetime.now(timezone.utc)
    formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Default metadata if none provided
    default_metadata = {"vector_name": vac, "source": "sunholo-cli", "eventTime": formatted_time}

    try:
        # Merge default metadata with provided metadata
        if metadata:
            if not isinstance(metadata, dict):
                metadata = json.loads(metadata)
        else:
            metadata = {}    
    except Exception as err:
        console.print(f"[bold red]ERROR: metadata not parsed: {err} for {metadata}")

    # Update metadata with default values if not present
    metadata.update(default_metadata)

    return metadata

def encode_data(vac, content, metadata=None, local_chunks=False):

    metadata = create_metadata(vac, metadata)

    # Encode the content (URL)
    if isinstance(content, str):
        message_data = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    else:
        raise ValueError(f"Unsupported content type: {type(content)}")

    now_utc = datetime.now(timezone.utc)
    formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Construct the message dictionary
    messageId = str(uuid.uuid4())
    message = {
        "message": {
            "data": message_data,
            "messageId": messageId,
            "publishTime": formatted_time,
            "attributes": {
                "namespace": vac,
                "return_chunks": str(local_chunks).lower()
            },
        }
    }

    # Merge metadata with attributes
    message["message"]["attributes"].update(metadata)

    #console.print()
    #console.print(f"Sending message: {messageId} with metadata:")
    #console.print(f"{message['message']['attributes']}")

    return message

def embed_command(args):
    chunk_args = vars(args).copy()
    embed_args = vars(args).copy()

    console.rule("Sending data for chunking")

    # Check if the data argument is a file path
    if args.is_file:
        file_path = Path(args.data)
        if not file_path.is_file():
            print(f"ERROR: The specified file does not exist: {file_path}")
            return

    if args.chunk_override:
        chunk_args["url_override"] = args.chunk_override
    else:
        chunk_args["vac_name"] = "chunker"
        chunk_args["url_override"] = ""
    chunk_args = Namespace(**chunk_args)
    chunk_url = resolve_service_url(chunk_args, no_config=True)

    with console.status(f"[bold orange]Sending '{args.data}' to chunk via {chunk_url}[/bold orange]", spinner="star"):
        if args.is_file:

            metadata = create_metadata(args.vac_name, args.metadata)  
            if args.local_chunks:
                metadata["return_chunks"] = True

            chunk_res = invoke_vac(f"{chunk_url}/direct_file_to_embed",
                                   data=file_path,
                                   vector_name=args.vac_name,
                                   metadata=metadata,
                                   is_file=True)
        
        else:
            json_data = encode_data(args.vac_name, args.data, args.metadata, args.local_chunks)
            console.print(f"Chunk JSON data: {json_data}")
            chunk_res = invoke_vac(f"{chunk_url}/pubsub_to_store", json_data)
        
        stop_proxy("chunker")
        if args.only_chunk:
            return chunk_res

        if not args.local_chunks:
            console.rule(f"Chunks sent for processing in cloud: {chunk_res}")

            return
    
    if not chunk_res:
        console.rule(f"[bold orange]No chunks were found for processing of {args.data}[/bold orange]")

        return
    
    console.rule("Processing chunks locally")

    if args.embed_override:
        embed_args["url_override"] = args.embed_override
    else:
        embed_args["vac_name"] = "embedder"
        embed_args["url_override"] = ""
    embed_args = Namespace(**embed_args)
    embed_url = resolve_service_url(embed_args, no_config=True)
    
    if not chunk_res:
        console.print(f"[bold red]ERROR: Did not get any chunks from {chunk_url} for {args.data}")
        stop_proxy("embedder")
        return

    chunks = chunk_res.get('chunks')
    if not chunks:
        console.print(f"[bold red]ERROR: No chunks found within json data: {str(chunk_res)} [/bold red]")
        stop_proxy("embedder")
        return
    
    embeds = []
    with Progress() as progress:
        task = progress.add_task(f"Embedding [{len(chunks)}] chunks via {embed_url}", total=len(chunks))
        for chunk in chunks:
            progress.console.print(f"Working on chunk {chunk['metadata']}")

            # do this async?
            content = chunk.get("page_content")
            now_utc = datetime.now(timezone.utc)
            formatted_time = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            chunk["metadata"]["eventTime"]  = formatted_time
            if not content:
                progress.console.print("[bold red]No content chunk found, skipping.[/bold red]")
                progress.advance(task)
                continue
            progress.console.print(f"Sending chunk length {len(content)} to embedder")
            processed_chunk = encode_data(vac = args.vac_name, 
                                          content = json.dumps(chunk))
            
            embed_res = invoke_vac(f"{embed_url}/embed_chunk", processed_chunk)
            embeds.append(embed_res)
            progress.advance(task)

    stop_proxy("embedder")
    console.rule("Embedding pipeline finished")
    
    return embed_res


def setup_embedder_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'embed' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    embed_parser = subparsers.add_parser('embed', help='Send data for embedding to a VAC vector store')
    embed_parser.add_argument('--embed-override', help='Override the embed VAC service URL.')
    embed_parser.add_argument('--chunk-override', help='Override the chunk VAC service URL.')
    embed_parser.add_argument('--no-proxy', action='store_true', help='Do not use the proxy and connect directly to the VAC service.')
    embed_parser.add_argument('-m', '--metadata', default=None, help='Metadata to send with the embedding (as JSON string).')
    embed_parser.add_argument('--local-chunks',  action='store_true', help='Whether to process chunks to embed locally, or via the cloud.')
    embed_parser.add_argument('vac_name', help='VAC service to embed the data for')
    embed_parser.add_argument('data', help='String content to send for embedding')
    embed_parser.add_argument('--is-file', action='store_true', help='Indicate if the data argument is a file path')
    embed_parser.add_argument('--only-chunk', action='store_true', help='Whether to only parse the document and return the chunks locally, with no embedding')

    embed_parser.set_defaults(func=embed_command)
