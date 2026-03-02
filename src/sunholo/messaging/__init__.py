#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Inter-agent messaging system powered by AILANG.

Provides a Python bridge to the AILANG messaging system for:
- Sending and receiving inter-agent messages
- Inbox management (read/unread/archive)
- GitHub issue synchronization
- Semantic search across messages

This module wraps the `ailang` CLI rather than reimplementing the
messaging system in Python, keeping the Go implementation as the
source of truth.

Requires: ailang CLI installed and available on PATH.
"""
