import subprocess

def get_local_gcloud_token():
    # Use gcloud credentials locally

    return (
        subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            stdout=subprocess.PIPE,
            check=True,
        )
        .stdout.strip()
        .decode()
    ) 