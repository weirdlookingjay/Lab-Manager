import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UsersProject.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from user_management.models import CustomUser

def create_agent_user():
    User = get_user_model()
    username = f"agent_{platform.node().lower()}"
    
    try:
        # Try to get existing user
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # Create new user if doesn't exist
        user = User.objects.create_user(
            username=username,
            email=f"{username}@local",
            password=None  # No password needed for agent
        )
        user.is_active = True
        user.save()
        
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    return token.key

if __name__ == "__main__":
    token = create_agent_user()
    
    # Create config.json
    config = {
        "server_url": "http://localhost:8000",  # Change this to your server URL
        "api_token": token
    }
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        
    print(f"Created config.json with token: {token}")
    print("Please update server_url in config.json if needed.")
