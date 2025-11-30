import random
from locust import HttpUser, task, between, events
from uuid import uuid4

class ChatUser(HttpUser):
    wait_time = between(1, 3)  # Simulate user thinking time between 1-3 seconds
    conversation_id = None
    user_id = None

    def on_start(self):
        """
        Executed when a simulated user starts.
        We create a conversation for this user to spam messages into.
        """
        self.user_id = str(uuid4())
        other_user = str(uuid4())
        
        # Create a conversation
        response = self.client.post("/conversations/", json={
            "type": "PRIVATE",
            "participants": [self.user_id, other_user],
            "metadata": {"source": "load_test"}
        })
        
        if response.status_code == 201:
            self.conversation_id = response.json()["id"]
        else:
            print(f"Failed to create conversation: {response.text}")

    @task(3)
    def send_text_message(self):
        """
        Send a simple text message. Higher weight (3).
        """
        if not self.conversation_id:
            return

        payload = {
            "conversation_id": self.conversation_id,
            "type": "TEXT",
            "content": f"Load test message from {self.user_id} - {random.randint(1, 1000)}"
        }
        
        with self.client.post("/messages/", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to send message: {response.status_code}")

    @task(1)
    def send_file_message(self):
        """
        Simulate file upload and sending. Lower weight (1).
        """
        if not self.conversation_id:
            return

        # 1. Get Upload URL
        file_payload = {
            "filename": "loadtest.png",
            "mime_type": "image/png",
            "size": 1024,
            "uploader_id": self.user_id
        }
        
        with self.client.post("/files/upload-url", json=file_payload, catch_response=True) as upload_resp:
            if upload_resp.status_code != 200:
                upload_resp.failure("Failed to get upload URL")
                return
            
            file_id = upload_resp.json()["file_id"]
            
            # 2. Send Message with File
            msg_payload = {
                "conversation_id": self.conversation_id,
                "type": "FILE",
                "content": "Image attachment",
                "file_id": file_id
            }
            
            with self.client.post("/messages/", json=msg_payload, catch_response=True) as msg_resp:
                if msg_resp.status_code == 201:
                    msg_resp.success()
                else:
                    msg_resp.failure(f"Failed to send file message: {msg_resp.status_code}")

