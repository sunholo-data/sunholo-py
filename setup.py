from setuptools import setup, find_packages

# Define your base version
version = '0.21.27'

setup(
    name='sunholo',
    version=version,
    packages=find_packages(),
    license='Apache License, Version 2.0',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    description='Large Language Model DevOps - a package to help deploy LLMs to the Cloud.',
    author = 'Holosun ApS',
    author_email = 'llmops@sunholo.com',
    url = 'https://github.com/sunholo-data/sunholo-py',
    download_url=f'https://github.com/sunholo-data/sunholo-py/archive/refs/tags/v{version}.tar.gz',
    keywords=['llms', 'devops','google_cloud_platform'],
    package_data={
        'sunholo.database': ['sql/sb/*.sql'],
        'sunholo.lookup': ['*.yaml']
    },
    install_requires=[
        # List your dependencies here
        "google-cloud-alloydb-connector[pg8000]",
        "google-cloud-logging",
        "google-cloud-storage",
        "lancedb",
        "langchain",
        "langchain-community",
        "langchain-openai",
        "langchain-google-genai",
        "pg8000",
        "sqlalchemy"
        # pydantic==1.10.13
        # "supabase",
        # "openai",
        # "tiktoken",
        # "google-cloud-storage",
        # "google-api-python-client",
        # "google-auth-httplib2",
        # "google-auth-oauthlib",
        # "psycopg2-binary"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',      # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Apache Software License', 
        'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],
)
