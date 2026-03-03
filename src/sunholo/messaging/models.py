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
Pydantic models for AILANG messaging system.

These models match the message format used by the ailang CLI,
enabling clean serialization/deserialization between Python and Go.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageStatus(str, Enum):
    """Message status in the inbox system."""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageType(str, Enum):
    """Message type categories."""
    GENERAL = "general"
    BUG = "bug"
    FEATURE = "feature"
    RESEARCH = "research"


class Message(BaseModel):
    """An inter-agent message in the AILANG messaging system."""
    id: str = ""
    inbox: str = ""
    title: str = ""
    body: str = ""
    from_agent: str = Field("", alias="from")
    to_inbox: str = Field("", alias="to")
    message_type: MessageType = Field(MessageType.GENERAL, alias="type")
    status: MessageStatus = MessageStatus.UNREAD
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    github_issue_url: str = ""
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a Message from a dictionary (e.g., parsed JSON from ailang CLI).

        Handles both Go-style field names and Python-style field names.
        """
        # Normalize field names from Go JSON output
        normalized = {}
        field_map = {
            "id": "id",
            "ID": "id",
            "inbox": "inbox",
            "Inbox": "inbox",
            "title": "title",
            "Title": "title",
            "body": "body",
            "Body": "body",
            "from": "from",
            "From": "from",
            "from_agent": "from",
            "to": "to",
            "To": "to",
            "to_inbox": "to",
            "type": "type",
            "Type": "type",
            "message_type": "type",
            "status": "status",
            "Status": "status",
            "created_at": "created_at",
            "CreatedAt": "created_at",
            "updated_at": "updated_at",
            "UpdatedAt": "updated_at",
            "github_issue_url": "github_issue_url",
            "GithubIssueURL": "github_issue_url",
            "tags": "tags",
            "Tags": "tags",
            "metadata": "metadata",
            "Metadata": "metadata",
        }

        for key, value in data.items():
            target = field_map.get(key, key)
            normalized[target] = value

        return cls(**normalized)
