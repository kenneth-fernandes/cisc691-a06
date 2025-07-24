"""
Core AI Agent implementation supporting multiple LLM providers
"""
import os
from typing import List, Dict, Any, Optional, Union
from datetime import date
from visa.models import VisaCategory, CountryCode, VisaBulletin, CategoryData, PredictionResult
from agent.visa_expertise import VISA_EXPERT_PROMPT, PROMPT_TEMPLATES, get_category_insight, get_country_insight
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# Import different LLM providers
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

class AIAgent:
    """Main AI Agent class that handles conversation and reasoning"""
    
    def __init__(self, provider: str = "openai", model_name: str = "gpt-4", temperature: float = 0.7, mode: str = "general"):
        """Initialize the AI Agent with specified provider and model"""
        self.mode = mode
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize LLM based on provider
        self.llm = self._initialize_llm()
        
        # Initialize conversation memory
        self.memory = ChatMessageHistory()
        
        # System prompt template
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """Create the system prompt that defines the agent's behavior"""
        if self.mode == "visa_expert":
            return VISA_EXPERT_PROMPT
        return """You are a helpful and intelligent AI assistant. You can:
        - Answer questions and provide information
        - Help with problem-solving and analysis
        - Assist with creative tasks and brainstorming
        - Maintain context throughout the conversation
        
        Always be helpful, accurate, and conversational in your responses."""
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on provider"""
        if self.provider == "openai":
            if ChatOpenAI is None:
                raise ImportError("langchain_openai not installed. Run: pip install langchain-openai")
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        elif self.provider == "anthropic":
            if ChatAnthropic is None:
                raise ImportError("langchain_anthropic not installed. Run: pip install langchain-anthropic")
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        elif self.provider == "google":
            if ChatGoogleGenerativeAI is None:
                raise ImportError("langchain_google_genai not installed. Run: pip install langchain-google-genai")
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        elif self.provider == "ollama":
            if ChatOllama is None:
                raise ImportError("langchain_community not installed. Run: pip install langchain-community")
            return ChatOllama(
                model=self.model_name,
                temperature=self.temperature
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    @staticmethod
    def get_supported_providers():
        """Get list of supported providers"""
        return ["openai", "anthropic", "google", "ollama"]
    
    def chat(self, user_input: str) -> str:
        """Process user input and return AI response"""
        try:
            # Create message template
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template("{input}")
            ])
            
            # Format the prompt with user input
            messages = prompt_template.format_messages(input=user_input)
            
            # Add conversation history if available
            history = self.memory.messages
            if history:
                messages = history + messages
            
            # Get response from LLM
            response = self.llm.invoke(messages)
            
            # Save to memory
            self.memory.add_user_message(user_input)
            self.memory.add_ai_message(response.content)
            
            return response.content
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Return the conversation history as a list of dictionaries"""
        history = []
        messages = self.memory.messages
        
        for message in messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
                
        return history
    
    def clear_history(self):
        """Clear the conversation history"""
        self.memory.clear()
    
    def update_system_prompt(self, new_prompt: str):
        """Update the system prompt"""
        self.system_prompt = new_prompt

    def _normalize_category_country(self, category: Union[str, VisaCategory], country: Union[str, CountryCode]) -> tuple[VisaCategory, CountryCode]:
        """Normalize category and country inputs to their enum types"""
        if isinstance(category, str):
            category = VisaCategory(category)
        if isinstance(country, str):
            country = CountryCode(country)
        return category, country

    def analyze_visa_movement(self, category: Union[str, VisaCategory], country: Union[str, CountryCode], 
                            start_date: date, end_date: date) -> str:
        """Analyze visa bulletin movement for a specific category and country"""
        category, country = self._normalize_category_country(category, country)

        template = PROMPT_TEMPLATES["analyze_movement"]
        prompt = template.format(
            category=category.value,
            country=country.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        cat_info = get_category_insight(category)
        country_info = get_country_insight(country)
        
        context = f"Category Info: {cat_info}\nCountry Info: {country_info}\n\n{prompt}"
        return self.chat(context)

    def predict_visa_movement(self, category: Union[str, VisaCategory], country: Union[str, CountryCode], 
                            months: int = 3) -> str:
        """Predict visa bulletin movement for the next few months"""
        category, country = self._normalize_category_country(category, country)

        template = PROMPT_TEMPLATES["predict_movement"]
        prompt = template.format(
            category=category.value,
            country=country.value,
            months=months
        )

        cat_info = get_category_insight(category)
        country_info = get_country_insight(country)
        
        context = f"Category Info: {cat_info}\nCountry Info: {country_info}\n\n{prompt}"
        return self.chat(context)

    def explain_visa_status(self, category: Union[str, VisaCategory], country: Union[str, CountryCode], 
                           bulletin: Optional[VisaBulletin] = None) -> str:
        """Explain current visa bulletin status for a category and country"""
        category, country = self._normalize_category_country(category, country)

        template = PROMPT_TEMPLATES["explain_status"]
        prompt = template.format(
            category=category.value,
            country=country.value
        )

        cat_info = get_category_insight(category)
        country_info = get_country_insight(country)
        
        if bulletin:
            cat_data = bulletin.get_category_data(category, country)
            if cat_data:
                prompt += f"\n\nCurrent Bulletin Data:\n{cat_data.to_dict()}"

        context = f"Category Info: {cat_info}\nCountry Info: {country_info}\n\n{prompt}"
        return self.chat(context)