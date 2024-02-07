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
from google.cloud import pubsub_v1
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import AlreadyExists
from google.auth import default

import json
import os
from ..logging import setup_logging
from ..utils.gcp import get_gcp_project

logging = setup_logging()

class PubSubManager:
    """
    Creates a new PubSub topic is necessary and sends pubsub messages to it
    """
    def __init__(self, memory_namespace: str, pubsub_topic: str=None, project_id: str=None, verbose:bool=False):
        self.project_id = project_id
        self.pubsub_topic = pubsub_topic
        self.publisher = None
        self.verbose = verbose
        self.memory_namespace = memory_namespace

        # Get the project ID from the default Google Cloud settings or the environment variable
        if self.project_id is None:
            _, project_id = default()
            self.project_id = project_id or get_gcp_project()

        if self.project_id:
            logging.info(f"Pubsub Project ID: {self.project_id}")
            # Create the Pub/Sub topic based on the project ID and memory_namespace
            self.publisher = pubsub_v1.PublisherClient()
            self.pubsub_topic = f"projects/{self.project_id}/topics/{pubsub_topic}"
            self._create_pubsub_topic_if_not_exists()

        else:
            # No project ID is available
            print("GOOGLE_CLOUD_PROJECT not set and gcloud default settings not available")

    def _create_pubsub_topic_if_not_exists(self):
        """Creates the Pub/Sub topic if it doesn't already exist."""
        try:
            # Check if the topic exists
            self.publisher.get_topic(request={"topic": self.pubsub_topic})
        except NotFound:
            # If the topic does not exist, create it
            self.publisher.create_topic(request={"name": self.pubsub_topic})
            logging.info(f"Created Pub/Sub topic: {self.pubsub_topic}")
            if self.verbose:
                print(f"Created Pub/Sub topic: {self.pubsub_topic}")
    
    def subscription_exists(self, subscription_name:str):

        full_subscription_name = f"projects/{self.project_id}/subscriptions/{subscription_name}"
        # Create a subscriber client
        subscriber = pubsub_v1.SubscriberClient()

        logging.debug(f"Checking subscription exists: {full_subscription_name}")
        
        # Check if the subscription already exists
        try:
            subscriber.get_subscription(full_subscription_name)
            logging.debug(f"Subscription {full_subscription_name} already exists.")
            return True
        except NotFound:
            return False
        except AlreadyExists:
            return True
        except Exception as e:
            logging.debug(f"Failed to get subscription: {e}")
            if self.verbose:
                print(f"Failed to get subscription: {e}")
            return False


    def create_subscription(self, subscription_name:str, push_endpoint: str):
            """
            Create a new subscription to the PubSub topic
            """

            if push_endpoint.startswith("https://"):
                logging.debug(f"Using full URL for push endpoint")
            else:
                raise ValueError("Push endpoint does not start with https://")

            # Create a subscriber client
            subscriber = pubsub_v1.SubscriberClient()
            
            # Create a push configuration
            push_config = pubsub_v1.types.PushConfig()
            push_config.push_endpoint = push_endpoint

            # Check if the subscription already exists
            exists = self.subscription_exists(subscription_name)

            if not exists:
                full_subscription_name = f"projects/{self.project_id}/subscriptions/{subscription_name}"
                logging.debug(f"Creating subscription {full_subscription_name}")
                try:
                    subscriber.create_subscription(name=full_subscription_name, 
                                                   topic=self.pubsub_topic, 
                                                   ack_deadline_seconds=600,
                                                   push_config=push_config)
                    logging.info(f"Created push subscription: {full_subscription_name}")
                    if self.verbose:
                        print(f"Created push subscription: {full_subscription_name}")
                except Exception as e:
                    logging.debug(f"Failed to create push subscription: {e}")
                    if self.verbose:
                        print(f"Failed to create push subscription: {e}")
            
            return full_subscription_name

    def _callback(self, future):
        try:
            message_id = future.result()
            logging.info(f"Published message with ID: {message_id} to {self.pubsub_topic} for {self.memory_namespace}")
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")

    def publish_message(self, message:str, verbose=False):
        """Publishes the given data to Google Pub/Sub."""

        if verbose or self.verbose:
            verbose = True
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        if self.publisher and self.pubsub_topic:
            message_bytes = message.encode('utf-8')
            future = self.publisher.publish(self.pubsub_topic, 
                                            message_bytes, 
                                            namespace = self.memory_namespace)
            future.add_done_callback(self._callback)

