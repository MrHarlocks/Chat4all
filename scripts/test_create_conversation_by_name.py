import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def login(name):
    print(f"Logging in as {name}...")
    response = requests.post(f"{BASE_URL}/users/login", json={"display_name": name})
    if response.status_code == 200:
        user = response.json()
        print(f"Logged in: {user['id']}")
        return user
    else:
        print(f"Login failed: {response.text}")
        sys.exit(1)

def create_conversation(user_id, participant_names):
    print(f"Creating conversation with participants: {participant_names}...")
    payload = {
        "type": "PRIVATE",
        "participant_names": participant_names,
        "participants": [] # Empty list of IDs
    }
    # Note: In a real app, we might need authentication headers. 
    # But currently the create_conversation endpoint doesn't seem to enforce auth token check, 
    # it just takes the request. 
    # Wait, the endpoint signature is:
    # async def create_conversation(request: CreateConversationRequest, service: ConversationService = Depends(ConversationService), user_service: UserService = Depends(UserService)):
    # It doesn't seem to require a logged in user context in the dependency injection for this specific endpoint yet, 
    # or maybe it does? Let's check the code I wrote.
    
    response = requests.post(f"{BASE_URL}/conversations/", json=payload)
    if response.status_code == 201:
        conv = response.json()
        print(f"Conversation created: {conv['id']}")
        return conv
    else:
        print(f"Create conversation failed: {response.text}")
        sys.exit(1)

def main():
    # 1. Create/Login User A
    user_a = login("Alice")
    
    # 2. Create/Login User B
    user_b = login("Bob")
    
    # 3. Alice creates conversation with Bob using name
    # The frontend logic adds the creator's name too.
    participant_names = ["Alice", "Bob"]
    
    create_conversation(user_a['id'], participant_names)
    
    print("Test passed!")

if __name__ == "__main__":
    main()
