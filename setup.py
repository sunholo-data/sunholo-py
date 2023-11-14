from setuptools import setup, find_packages
import datetime

# Define your base version
base_version = '0.1.0'

timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
version = f"{base_version}.{timestamp}"


setup(
    name='llmops',
    version=version,
    packages=find_packages(),
    package_data={
        'llmops.database': ['sql/sb/*.sql']
    },
    install_requires=[
        # List your dependencies here
        "langchain"
        # "supabase",
        # "openai",
        # "tiktoken",
        # "google-cloud-storage",
        # "google-api-python-client",
        # "google-auth-httplib2",
        # "google-auth-oauthlib",
        # "psycopg2-binary"
    ],
)
