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
Multi-channel messaging integration for sunholo.

Provides a unified channel abstraction for receiving and sending messages
across multiple platforms:
- Email (SendGrid/Mailgun webhook integration)
- Telegram (Bot API integration)
- WhatsApp (Twilio integration)

Each channel implements a common interface for:
- Receiving webhooks
- Sending responses (with platform-specific formatting)
- Session management
- Rate limiting

Install with: pip install sunholo[channels]
"""
