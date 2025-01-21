# from https://github.com/ray-project/docu-mentor
import base64
import httpx
from dotenv import load_dotenv
import jwt
import os
import time

load_dotenv()



APP_ID = os.environ.get("APP_ID")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "")

# with open('private-key.pem', 'r') as f:
#     PRIVATE_KEY = f.read()

def generate_jwt():
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID,
    }
    if PRIVATE_KEY:
        jwt_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
        return jwt_token
    raise ValueError("PRIVATE_KEY not found.")


async def get_installation_access_token(jwt, installation_id):
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Accept": "application/vnd.github.v3+json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        return response.json()["token"]


def get_diff_url(pr):
    """GitHub 302s to this URL."""
    original_url = pr.get("url")
    parts = original_url.split("/")
    owner, repo, pr_number = parts[-4], parts[-3], parts[-1]
    return f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{pr_number}.diff"


async def get_branch_files(pr, branch, headers):
    original_url = pr.get("url")
    parts = original_url.split("/")
    owner, repo = parts[-4], parts[-3]
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        tree = response.json().get('tree', [])
        files = {}
        for item in tree:
            if item['type'] == 'blob':
                file_url = item['url']
                print(file_url)
                file_response = await client.get(file_url, headers=headers)
                content = file_response.json().get('content', '')
                # Decode the base64 content
                decoded_content = base64.b64decode(content).decode('utf-8')
                files[item['path']] = decoded_content
        return files


async def get_pr_head_branch(pr, headers):
    original_url = pr.get("url")
    parts = original_url.split("/")
    owner, repo, pr_number = parts[-4], parts[-3], parts[-1]
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        # Check if the response is successful
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response body:", response.text)
            return ''

        # Safely get the 'ref'
        data = response.json()
        head_data = data.get('head', {})
        ref = head_data.get('ref', '')
        return ref


def files_to_diff_dict(diff):
    files_with_diff = {}
    current_file = None
    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            current_file = line.split(" ")[2][2:]
            files_with_diff[current_file] = {"text": []}
        elif line.startswith("+") and not line.startswith("+++"):
            files_with_diff[current_file]["text"].append(line[1:])
    return files_with_diff


def parse_diff_to_line_numbers(diff):
    files_with_line_numbers = {}
    current_file = None
    line_number = 0
    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            current_file = line.split(" ")[2][2:]
            files_with_line_numbers[current_file] = []
            line_number = 0
        elif line.startswith("@@"):
            line_number = int(line.split(" ")[2].split(",")[0][1:]) - 1
        elif line.startswith("+") and not line.startswith("+++"):
            files_with_line_numbers[current_file].append(line_number)
            line_number += 1
        elif not line.startswith("-"):
            line_number += 1
    return files_with_line_numbers


def get_context_from_files(files, files_with_line_numbers, context_lines=2):
    context_data = {}
    for file, lines in files_with_line_numbers.items():
        file_content = files[file].split("\n")
        context_data[file] = []
        for line in lines:
            start = max(line - context_lines, 0)
            end = min(line + context_lines + 1, len(file_content))
            context_data[file].append('\n'.join(file_content[start:end]))
    return context_data

app = FastAPI()


async def handle_webhook(request: Request):
    data = await request.json()

    installation = data.get("installation")
    if installation and installation.get("id"):
        installation_id = installation.get("id")
        logger.info(f"Installation ID: {installation_id}")

        JWT_TOKEN = generate_jwt()

        installation_access_token = await get_installation_access_token(
            JWT_TOKEN, installation_id
        )

        headers = {
            "Authorization": f"token {installation_access_token}",
            "User-Agent": "docu-mentor-bot",
            "Accept": "application/vnd.github.VERSION.diff",
        }
    else:
        raise ValueError("No app installation found.")

    # If PR exists and is opened
    if "pull_request" in data.keys() and (
        data["action"] in ["opened", "reopened"]
    ):  # use "synchronize" for tracking new commits
        pr = data.get("pull_request")

        # Greet the user and show instructions.
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{pr['issue_url']}/comments",
                json={"body": GREETING},
                headers=headers,
            )
        return JSONResponse(content={}, status_code=200)

    # Check if the event is a new or modified issue comment
    if "issue" in data.keys() and data.get("action") in ["created", "edited"]:
        issue = data["issue"]

        # Check if the issue is a pull request
        if "/pull/" in issue["html_url"]:
            pr = issue.get("pull_request")

            # Get the comment body
            comment = data.get("comment")
            comment_body = comment.get("body")
            # Remove all whitespace characters except for regular spaces
            comment_body = comment_body.translate(
                str.maketrans("", "", string.whitespace.replace(" ", ""))
            )

            # Skip if the bot talks about itself
            author_handle = comment["user"]["login"]

            # Check if the bot is mentioned in the comment
            if (
                author_handle != "docu-mentor[bot]"
                and "@docu-mentor run" in comment_body
            ):
                async with httpx.AsyncClient() as client:
                    # Fetch diff from GitHub
                    files_to_keep = comment_body.replace(
                        "@docu-mentor run", ""
                    ).split(" ")
                    files_to_keep = [item for item in files_to_keep if item]

                    logger.info(files_to_keep)

                    url = get_diff_url(pr)
                    diff_response = await client.get(url, headers=headers)
                    diff = diff_response.text

                    files_with_lines = parse_diff_to_line_numbers(diff)

                    # Get head branch of the PR
                    headers["Accept"] = "application/vnd.github.full+json"
                    head_branch = await get_pr_head_branch(pr, headers)

                    # Get files from head branch
                    head_branch_files = await get_branch_files(pr, head_branch, headers)
                    print("HEAD FILES", head_branch_files)

                    # Enrich diff data with context from the head branch.
                    context_files = get_context_from_files(head_branch_files, files_with_lines)

                    # Filter the dictionary
                    if files_to_keep:
                        context_files = {
                            k: context_files[k]
                            for k in context_files
                            if any(sub in k for sub in files_to_keep)
                        }

                    # Get suggestions from Docu Mentor
                    content, model, prompt_tokens, completion_tokens = \
                        ray_mentor(context_files) if ray.is_initialized() else mentor(context_files)


                    # Let's comment on the PR
                    await client.post(
                        f"{comment['issue_url']}/comments",
                        json={
                            "body": f":rocket: Docu Mentor finished "
                            + "analysing your PR! :rocket:\n\n"
                            + "Take a look at your results:\n"
                            + f"{content}\n\n"
                            + "This bot is  powered by "
                            + "[Sunholo Multivac](https://www.sunholo.com/).\n"
                            + f"It used the model {model}, used {prompt_tokens} prompt tokens, "
                            + f"and {completion_tokens} completion tokens in total."
                        },
                        headers=headers,
                    )

@serve.deployment(route_prefix="/")
@serve.ingress(app)
class ServeBot:
    @app.get("/")
    async def root(self):
        return {"message": "Docu Mentor reporting for duty!"}

    @app.post("/webhook/")
    async def handle_webhook_route(self, request: Request):
        return await handle_webhook(request)

