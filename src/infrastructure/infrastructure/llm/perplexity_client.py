from infrastructure.llm.base_llm_client import BaseLLMClient
from infrastructure.config.settings import Settings
import yaml
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict

class PerplexityLLMClient(BaseLLMClient):
    """
    Handles LLM invocation using LangChain and Perplexity, with prompt templating.
    """
    def __init__(self, prompt_path: str, settings: Settings):
        """
        :param prompt_path: Path to the YAML prompt template
        :param settings: Pydantic Settings object
        """
        self.prompt_path = prompt_path
        self.settings = settings
        self._load_prompt()

    def _load_prompt(self) -> None:
        """
        Load the system and user prompt templates from YAML.
        """
        with open(self.prompt_path, 'r') as f:
            prompt_yaml = yaml.safe_load(f)
        self.system_template = prompt_yaml['system']
        self.user_template = prompt_yaml['user']

    def get_rename_map(self, files: List[str], album_name: str, language: str) -> Dict[str, Dict[str, str]]:
        """
        Call the LLM to get a mapping of old to new filenames.
        :param files: List of filenames
        :param album_name: Album name
        :param language: Language for official track names
        :return: Dict with 'old_to_new' mapping
        """
        system_prompt = self.system_template.replace("{{ language }}", language)
        user_prompt = self.user_template.replace("{{ album_name }}", album_name).replace("{{ files }}", str(files)).replace("{{ language }}", language)

        llm = ChatOpenAI(
            api_key=self.settings.perplexity_api_key,
            base_url=self.settings.base_url,
            model=self.settings.model,
            temperature=0.0,
        )
        parser = JsonOutputParser()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = llm.invoke(messages)
        return parser.parse(response.content) 