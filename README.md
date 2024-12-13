[![PyPi Version](https://img.shields.io/pypi/v/sunholo.svg)](https://pypi.python.org/pypi/sunholo/)

## Introduction
This is the Sunholo Python project, a comprehensive toolkit for working with language models and vector stores on Google Cloud Platform. It provides a wide range of functionalities and utilities to facilitate the development and deployment of language model applications.

Please refer to the website for full documentation at https://dev.sunholo.com/

## Listen to the audio file:

A [NotebookLM](https://notebooklm.google/) generated podcast of the codebase that may help give you an overview of what the library is capable of:

[Listen to the audio file from Google Drive](https://drive.google.com/file/d/1GvwRmiYDjPjN2hXQ8plhnVDByu6TmgCQ/view?usp=drive_link) or on the website at https://dev.sunholo.com/docs/ 

> "Ever wish you could build your own AI?..."

## Tests via pytest

If loading from GitHub, run tests:

```bash
pip install pytest
pip install . --use-feature=in-tree-build
pytest tests
```

## Local dev

```sh
uv tool install --from "sunholo[cli]" sunholo --with ".[all]"
```

## Demos

Using https://github.com/charmbracelet/vhs

```sh
vhs record > cassette.tape
```

Then make gif:

```sh
vhs docs/tapes/config-list.tape
```



```
   Copyright [2024] [Holosun ApS]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

