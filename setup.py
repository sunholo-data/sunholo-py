from setuptools import setup, find_packages

version = '0.118.0'

setup(
    name='sunholo',
    version=version,
    packages=find_packages(),
    license='Apache License, Version 2.0',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    description='Large Language Model DevOps - a package to help deploy LLMs to the Cloud.',
    author = 'Holosun ApS',
    author_email = 'multivac@sunholo.com',
    url = 'https://github.com/sunholo-data/sunholo-py',
    download_url=f'https://github.com/sunholo-data/sunholo-py/archive/refs/tags/v{version}.tar.gz',
    keywords=['llms', 'devops','google_cloud_platform'],
    entry_points={
        'console_scripts': [
            'sunholo=sunholo.cli.cli:main', 
        ],
    },
    package_data={
        'sunholo.database': ['sql/sb/*.sql'],
        'sunholo.lookup': ['*.yaml'],
        'sunholo.templates' : ['*.*']
    },
    install_requires=[
        # Base dependencies
        "aiohttp",
        "google-auth", # to check if on gcp
        "pydantic",
        "requests",
        "ruamel.yaml",
        "tenacity"
    ],
    extras_require={
        # Define optional dependencies with feature names
        'all': [
            "aiohttp",
            "anthropic[vertex]",
            "asyncpg",
            "azure-identity",
            "azure-storage-blob",
            "fastapi",
            "flask",
            "google-auth",
            "google-auth-httplib2",
            "google-auth-oauthlib",
            "google-cloud-aiplatform>=1.58.0",
            "google-api-python-client",
            "google-cloud-alloydb-connector[pg8000]",
            "google-cloud-bigquery",
            "google-cloud-build",
            "google-cloud-service-control",
            "google-cloud-logging",
            "google-cloud-storage",
            "google-cloud-pubsub",
            "google-cloud-discoveryengine",
            "google-cloud-texttospeech",
            "google-generativeai>=0.7.1",
            "google-genai",
            "gunicorn",
            "httpcore",
            "httpx",
            "jsonschema",
            "lancedb",
            "langchain>=0.2.16",
            "langchain-experimental>=0.0.61",
            "langchain-community>=0.2.11",
            "langchain-openai==0.1.25",
            "langchain-google-genai==1.0.10",
            "langchain_google_alloydb_pg",
            "langchain-anthropic==0.1.23",
            "langchain-google-vertexai",
            "langchain-unstructured",
            "langfuse",
            "mcp",
            "numpy",
            "opencv-python",
            "pg8000",
            "pgvector",
            "pillow",
            "playwright",
            "psutil",
            "psycopg2-binary",
            "pydantic",
            "pypdf",
            "python-hcl2",
            "python-socketio",
            "pytesseract",
            "requests",
            "rich",
            "sounddevice",
            "supabase",
            "tabulate",
            "tantivy",
            "tenacity",
            "tiktoken",
            "unstructured[local-inference,all-docs]",
            "xlwings"
        ],
        'langchain': [
            "langchain",
            "langchain_experimental",
            "langchain-community",
            "langsmith",
        ],
        'azure': [
            "azure-identity",
            "azure-storage-blob"
        ],
        'cli': [
            "jsonschema>=4.21.1",
            "rich"
        ],
        'database': [
            "asyncpg",
            "supabase",
            "sqlalchemy",
            "pg8000",
            "pgvector",
            "psycopg2-binary",
            "lancedb",
            "tantivy"
        ],
        'pipeline': [
            "GitPython",
            "lark",
            "langchain>=0.2.16",
            "langchain-unstructured",
            "psutil",
            "pypdf",
            "pytesseract",
            "tabulate",
            "unstructured[local-inference,all-docs]"
        ],
        'gcp': [
            "anthropic[vertex]",
            "google-api-python-client",
            "google-auth-httplib2",
            "google-auth-oauthlib",
            "google-cloud-alloydb-connector[pg8000]",
            "google-cloud-aiplatform>=1.58.0",
            "google-cloud-bigquery",
            "google-cloud-build",
            "google-cloud-service-control",
            "google-cloud-storage",
            "google-cloud-logging",
            "google-cloud-pubsub",
            "google-cloud-discoveryengine",
            "google-cloud-texttospeech",
            "google-genai",
            "google-generativeai>=0.8.3",
            "langchain-google-genai>=2.0.0",
            "langchain_google_alloydb_pg>=0.2.2",
            "langchain-google-vertexai",
            "pillow",
        ],
        'openai': [
            "langchain-openai==0.1.25",
            "tiktoken"
        ],
        'anthropic': [
            "langchain-anthropic>=0.1.23",
            "mcp"
        ],
        'tools' : [
            'openapi-spec-validator',
            'playwright'
        ],
        'http': [
            "fastapi",
            "flask",
            "gunicorn",
            "httpcore",
            "httpx",
            "langfuse",
            "python-socketio",
            "requests",
            "tenacity"
        ],
        'excel': [
            'xlwings',
            'requests',
            'rich'
        ],
        'iac':[
            'python-hcl2'
        ],
        'tts':[
            'google-cloud-texttospeech',
            'numpy',
            'sounddevice',
        ],
        'video':[
            'opencv-python'
        ]
        

    },
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',     
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Apache Software License', 
        'Programming Language :: Python :: 3', 
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],
)
