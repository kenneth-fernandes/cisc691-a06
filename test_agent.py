"""
Simple test script for the AI Agent
"""
import os
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
from src.agent.factory import create_agent

def test_agent():
    """Test the AI agent functionality"""
    try:
        # Initialize agent with configured provider
        from src.utils.config import get_config
        config = get_config()
        print("\n🚀 Initializing AI Agent...")
        print(f"📊 Provider: {config.LLM_PROVIDER}")
        print(f"🔄 Available providers: {config.get_supported_providers()}\n")
        
        agent = create_agent("default")
        print("✅ Agent created successfully")
        print(f"🔧 Using provider: {agent.provider}")
        print(f"🤖 Using model: {agent.model_name}\n")
        
        print("💬 Starting conversation test...\n")
        
        # Test basic introduction
        print("👤 User: Hello! Can you introduce yourself?")
        start_time = time.time()
        response = agent.chat("Hello! Can you introduce yourself?")
        end_time = time.time()
        print(f"🤖 Agent: {response}")
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds\n")
        
        # Test capabilities explanation
        print("👤 User: What specific tasks can you help me with?")
        start_time = time.time()
        response2 = agent.chat("What specific tasks can you help me with?")
        end_time = time.time()
        print(f"🤖 Agent: {response2}")
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds\n")
        
        print("📜 Conversation History:")
        history = agent.get_conversation_history()
        for i, msg in enumerate(history, 1):
            role = "👤 User" if msg["role"] == "user" else "🤖 Agent"
            print(f"{i}. {role}: {msg['content']}")
        
    except Exception as e:
        print(f"❌ Error testing agent: {e}")

if __name__ == "__main__":
    test_agent()