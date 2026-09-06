from litellm import completion
from dotenv import load_dotenv
import os
from src.utils.config_loader import load_config
load_dotenv()

class ApiKeyManager:
    def __init__(self):
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        
class ModelLoader:
    def __init__(self):
        self.api_key_mgr = ApiKeyManager()
        self.config = load_config()
        
    def load_llm(self,provider:str):
        api_key = None 
        model = None
        if provider.capitalize() == "Anthropic":
            api_key = self.api_key_mgr.ANTHROPIC_API_KEY
            model = self.config["llm"]["Anthropic"]["model_name"]
        elif provider.lower() == "groq":
            api_key = self.api_key_mgr.GROQ_API_KEY
            model = self.config["llm"]["groq"]["model_name"]
        return api_key,model
        
        
        
            
    
    
        


