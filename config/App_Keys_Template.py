from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_KEY')

# Template: replace the placeholders with your actual API keys
# GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
# TWITTER_API_KEY=your_twitter_api_key_here
# FACEBOOK_API_KEY=your_facebook_api_key_here
