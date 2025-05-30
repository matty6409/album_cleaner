from infrastructure.llm.base_llm_client import BaseLLMClient
from infrastructure.config.settings import Settings
import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.llms.deepseek import DeepSeekLLM
from typing import List, Dict

class DeepSeekLLMClient(BaseLLMClient):
    def __init__(self, prompt_path: str, settings: Settings):
        self.prompt_path = prompt_path
        self.settings = settings
        self._load_prompt()

    def _load_prompt(self) -> None:
        with open(self.prompt_path, 'r') as f:
            prompt_yaml = yaml.safe_load(f)
        self.system_template = prompt_yaml['system']
        self.user_template = prompt_yaml['user']

    def get_rename_map(self, files: List[str], album_name: str, language: str) -> Dict[str, Dict[str, str]]:
        system_prompt = self.system_template.replace("{{ language }}", language)
        user_prompt = self.user_template.replace("{{ album_name }}", album_name).replace("{{ files }}", str(files)).replace("{{ language }}", language)

        llm = DeepSeekLLM(
            api_key=self.settings.deepseek_api_key,  # Add this to your settings
            model=self.settings.deepseek_model,      # Add this to your settings
            temperature=0.0,
        )
        parser = JsonOutputParser()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = llm.invoke(messages)
        return parser.parse(response.content)
