#!/usr/bin/env python3
"""
Test script for Visa Analytics Integration

This script tests the integration between the AI agent and visa analytics system,
verifying that issues #25 and #27 are properly implemented.
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent.core import AIAgent
from agent.data_bridge import get_visa_data_bridge
from agent.visa_tools import get_visa_analytics_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_bridge():
    """Test the visa data bridge functionality"""
    print("🔗 Testing Visa Data Bridge...")
    
    bridge = get_visa_data_bridge()
    
    # Test data availability
    availability = bridge.check_data_availability()
    print(f"Data Availability: {availability}")
    
    # Test context extraction
    test_queries = [
        "How is EB-2 India trending?",
        "Compare EB categories for China",
        "Predict EB-1 movement for next 3 months",
        "Give me a summary of all visa categories",
        "What's the weather like today?"  # Non-visa query
    ]
    
    for query in test_queries:
        context = bridge.extract_visa_context(query)
        print(f"Query: '{query}'")
        print(f"Context: {context}")
        print("-" * 50)


def test_visa_tools():
    """Test individual visa analytics tools"""
    print("\n🛠️ Testing Visa Analytics Tools...")
    
    tools = get_visa_analytics_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    # Test trend analysis tool
    try:
        from agent.visa_tools import VisaTrendAnalysisTool
        trend_tool = VisaTrendAnalysisTool()
        result = trend_tool._run("EB-2", "INDIA", 3)
        print(f"Trend Analysis Result (first 500 chars): {result[:500]}...")
    except Exception as e:
        print(f"Trend analysis test failed: {e}")
    
    # Test category comparison tool
    try:
        from agent.visa_tools import VisaCategoryComparisonTool
        comparison_tool = VisaCategoryComparisonTool()
        result = comparison_tool._run("INDIA", ["EB-1", "EB-2", "EB-3"], 2)
        print(f"Category Comparison Result (first 500 chars): {result[:500]}...")
    except Exception as e:
        print(f"Category comparison test failed: {e}")


def test_agent_integration():
    """Test the full agent integration with visa tools"""
    print("\n🤖 Testing Agent Integration...")
    
    # Initialize agent in visa expert mode
    try:
        agent = AIAgent(provider="google", model_name="gemini-pro", mode="visa_expert")
        print(f"Agent initialized with {len(agent.visa_tools)} tools")
        print(f"Agent executor available: {agent.agent_executor is not None}")
        print(f"Data bridge available: {hasattr(agent, 'data_bridge')}")
        if hasattr(agent, 'data_bridge'):
            print(f"Data bridge status: {agent.data_bridge.is_available}")
        
        # Test queries
        test_queries = [
            "How is EB-2 India trending historically?",
            "Compare EB-1, EB-2, and EB-3 for China",
            "What's the prediction for EB-2 India next 3 months?",
            "Give me a summary of visa bulletin trends",
            "Explain the current status of EB-1 category"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            print("=" * 60)
            
            try:
                response = agent.chat(query)
                print(f"Response (first 800 chars): {response[:800]}...")
                
                if len(response) > 800:
                    print("[Response truncated for readability]")
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")


def test_error_handling():
    """Test error handling and fallback mechanisms"""
    print("\n🛡️ Testing Error Handling...")
    
    # Test with invalid inputs
    try:
        from agent.visa_tools import VisaTrendAnalysisTool
        trend_tool = VisaTrendAnalysisTool()
        
        # Test invalid category
        result = trend_tool._run("INVALID_CATEGORY", "INDIA", 3)
        print(f"Invalid category test: {result[:200]}...")
        
        # Test invalid country
        result = trend_tool._run("EB-2", "INVALID_COUNTRY", 3)
        print(f"Invalid country test: {result[:200]}...")
        
    except Exception as e:
        print(f"Error handling test result: {e}")


def test_data_context_injection():
    """Test data context injection functionality"""
    print("\n💉 Testing Data Context Injection...")
    
    bridge = get_visa_data_bridge()
    
    test_cases = [
        ("How is EB-2 India trending?", "You are a visa expert."),
        ("What's the weather like?", "You are a visa expert."),
        ("Compare EB categories for China", "You are a visa expert.")
    ]
    
    for query, base_prompt in test_cases:
        enhanced_prompt = bridge.inject_data_context(query, base_prompt)
        
        print(f"Query: {query}")
        print(f"Enhanced prompt length: {len(enhanced_prompt)} chars")
        print(f"Data injected: {'RELEVANT VISA DATA' in enhanced_prompt}")
        print("-" * 50)


def main():
    """Run all integration tests"""
    print("🚀 Starting Visa Analytics Integration Tests")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    print("=" * 80)
    
    try:
        # Test 1: Data Bridge
        test_data_bridge()
        
        # Test 2: Visa Tools
        test_visa_tools()
        
        # Test 3: Agent Integration
        test_agent_integration()
        
        # Test 4: Error Handling
        test_error_handling()
        
        # Test 5: Data Context Injection
        test_data_context_injection()
        
        print("\n✅ All tests completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)