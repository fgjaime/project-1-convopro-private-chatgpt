from llama_index.llms.ollama import Ollama
from config.settings import Settings

settings = Settings()
OLLAMA_URL = settings.OLLAMA_URL

# Module-level cache for model and instance
_current_model_name = None
_current_llm_instance = None

def get_ollama_llm(model_name: str):
    global _current_model_name, _current_llm_instance
    if _current_model_name == model_name and _current_llm_instance is not None:
        return _current_llm_instance
    llm = Ollama(base_url=OLLAMA_URL, model=model_name)
    _current_model_name = model_name
    _current_llm_instance = llm
    return _current_llm_instance

# Example of usage
# check_llm = get_ollama_llm(model_name="llama3:latest")
# print(check_llm)
# print(type(check_llm))