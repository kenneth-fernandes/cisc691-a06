"""
Core AI Agent implementation supporting multiple LLM providers
"""
import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import date
from visa.models import VisaCategory, CountryCode, VisaBulletin, CategoryData, PredictionResult
from agent.visa_expertise import VISA_EXPERT_PROMPT, PROMPT_TEMPLATES, get_category_insight, get_country_insight
from agent.visa_tools import get_visa_analytics_tools
from agent.data_bridge import get_visa_data_bridge
from utils.config import get_config
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts import PromptTemplate

# Try to import agent components, with fallback
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    try:
        from langchain_community.agents import create_tool_calling_agent, AgentExecutor
    except ImportError:
        create_tool_calling_agent = None
        AgentExecutor = None

logger = logging.getLogger(__name__)

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
    """Main AI Agent class that handles conversation and reasoning with visa analytics integration"""
    
    def __init__(self, provider: str = "openai", model_name: str = "gpt-4", temperature: float = 0.7, mode: str = "general"):
        """Initialize the AI Agent with specified provider and model"""
        self.mode = mode
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        
        # Load configuration
        self.config = get_config()
        
        # Initialize LLM based on provider
        self.llm = self._initialize_llm()
        
        # Initialize conversation memory
        self.memory = ChatMessageHistory()
        
        # Initialize visa analytics integration first (needed for system prompt)
        self.data_bridge = get_visa_data_bridge()
        self.visa_tools = get_visa_analytics_tools() if mode == "visa_expert" else []
        
        # System prompt template (after data_bridge is initialized)
        self.system_prompt = self._create_system_prompt()
        
        # Initialize agent executor for tool-calling if in visa expert mode
        self.agent_executor = None
        if mode == "visa_expert" and self.visa_tools:
            try:
                self._initialize_agent_executor()
                logger.info("Visa analytics tools integrated successfully")
            except Exception as e:
                logger.error(f"Failed to initialize agent executor: {e}")
                self.visa_tools = []
        
    def _create_system_prompt(self) -> str:
        """Create the system prompt that defines the agent's behavior"""
        if self.mode == "visa_expert":
            # Enhanced system prompt for visa expert mode with tools
            base_prompt = VISA_EXPERT_PROMPT
            
            # Add data availability context
            data_summary = self.data_bridge.get_data_summary_for_context()
            
            enhanced_prompt = f"""{base_prompt}

=== DATA ACCESS CAPABILITIES ===
{data_summary}

When users ask about visa trends, predictions, or comparisons, I can access real historical data using specialized tools:
- visa_trend_analysis: For analyzing historical trends of specific categories and countries
- visa_category_comparison: For comparing categories within a country
- visa_movement_prediction: For predicting future movements
- visa_summary_report: For comprehensive market overviews

I will use these tools to provide data-driven responses whenever possible.
==="""
            return enhanced_prompt
        
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
                temperature=self.temperature,
                base_url=self.config.OLLAMA_BASE_URL
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _initialize_agent_executor(self):
        """Initialize the agent executor for tool-calling capabilities"""
        if not self.visa_tools or create_tool_calling_agent is None or AgentExecutor is None:
            logger.warning("LangChain agent components not available, using manual tool integration")
            return
        
        # Create a prompt template for the agent
        prompt = PromptTemplate.from_template("""
{system_prompt}

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}""")
        
        # Create the agent
        try:
            agent = create_tool_calling_agent(
                llm=self.llm,
                tools=self.visa_tools,
                prompt=prompt
            )
            
            # Create the executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.visa_tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            # Fallback to simple tool integration
            self.agent_executor = None
    
    @staticmethod
    def get_supported_providers():
        """Get list of supported providers"""
        return ["openai", "anthropic", "google", "ollama"]
    
    def chat(self, user_input: str) -> str:
        """Process user input and return AI response with visa analytics integration"""
        try:
            # Check for data unavailability scenarios first
            if self.mode == "visa_expert":
                unavailable_response = self.data_bridge.handle_data_unavailable_scenario(user_input)
                if unavailable_response:
                    self.memory.add_user_message(user_input)
                    self.memory.add_ai_message(unavailable_response)
                    return unavailable_response
            
            # Use agent executor for visa expert mode with tools
            if self.mode == "visa_expert" and self.agent_executor:
                try:
                    # Try using the agent executor with tools
                    result = self.agent_executor.invoke({
                        "input": user_input,
                        "system_prompt": self.system_prompt
                    })
                    
                    response_content = result.get("output", str(result))
                    
                    # Save to memory
                    self.memory.add_user_message(user_input)
                    self.memory.add_ai_message(response_content)
                    
                    return response_content
                    
                except Exception as tool_error:
                    logger.warning(f"Tool execution failed, falling back to manual tool integration: {tool_error}")
                    # Fall through to manual tool integration
            
            # Manual tool integration for visa expert mode (fallback)
            if self.mode == "visa_expert" and self.visa_tools:
                tool_response = self._manual_tool_integration(user_input)
                if tool_response:
                    self.memory.add_user_message(user_input)
                    self.memory.add_ai_message(tool_response)
                    return tool_response
            
            # Regular chat processing with data context injection
            enhanced_prompt = self.system_prompt
            if self.mode == "visa_expert":
                enhanced_prompt = self.data_bridge.inject_data_context(user_input, self.system_prompt)
            
            # Create message template
            prompt_template = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(enhanced_prompt),
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
            logger.error(f"Error in chat processing: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _manual_tool_integration(self, user_input: str) -> Optional[str]:
        """Manual tool integration when agent executor is not available"""
        try:
            # Extract context from user query
            context = self.data_bridge.extract_visa_context(user_input)
            
            if not context['is_visa_related']:
                return None
            
            # Determine which tool to use based on query type
            if context['query_type'] == 'trend_analysis' and context['categories'] and context['countries']:
                # Use trend analysis tool
                from agent.visa_tools import VisaTrendAnalysisTool
                tool = VisaTrendAnalysisTool()
                return tool._run(context['categories'][0], context['countries'][0])
            
            elif context['query_type'] == 'comparison' and context['countries']:
                # Use category comparison tool
                from agent.visa_tools import VisaCategoryComparisonTool
                tool = VisaCategoryComparisonTool()
                return tool._run(context['countries'][0], context['categories'] if context['categories'] else None)
            
            elif context['query_type'] == 'prediction' and context['categories'] and context['countries']:
                # Use prediction tool
                from agent.visa_tools import VisaMovementPredictionTool
                tool = VisaMovementPredictionTool()
                return tool._run(context['categories'][0], context['countries'][0])
            
            elif context['query_type'] == 'summary':
                # Use summary report tool
                from agent.visa_tools import VisaSummaryReportTool
                tool = VisaSummaryReportTool()
                return tool._run(context['categories'] if context['categories'] else None,
                               context['countries'] if context['countries'] else None)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in manual tool integration: {e}")
            return None
    
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