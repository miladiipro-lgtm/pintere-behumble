#!/usr/bin/env python3
"""
Test script for Pinterest scraper to identify issues
"""
import sys
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required packages can be imported."""
    try:
        import requests
        logger.info("✅ requests imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import requests: {e}")
        return False
    
    try:
        import beautifulsoup4
        logger.info("✅ beautifulsoup4 imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import beautifulsoup4: {e}")
        return False
    
    try:
        import pandas
        logger.info("✅ pandas imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import pandas: {e}")
        return False
    
    try:
        import emoji
        logger.info("✅ emoji imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import emoji: {e}")
        return False
    
    return True

def test_file_operations():
    """Test basic file operations."""
    try:
        # Test creating output directory
        os.makedirs("test_output", exist_ok=True)
        logger.info("✅ Output directory creation successful")
        
        # Test file writing
        test_file = "test_output/test.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        logger.info("✅ File writing successful")
        
        # Clean up
        os.remove(test_file)
        os.rmdir("test_output")
        logger.info("✅ File cleanup successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ File operations failed: {e}")
        return False

def test_network():
    """Test basic network connectivity."""
    try:
        import requests
        response = requests.get("https://httpbin.org/get", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Network connectivity successful")
            return True
        else:
            logger.error(f"❌ Network request failed with status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Network test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🧪 Starting Pinterest scraper tests...")
    
    tests = [
        ("Package Imports", test_imports),
        ("File Operations", test_file_operations),
        ("Network Connectivity", test_network)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing: {test_name} ---")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} PASSED")
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The environment looks good.")
        return 0
    else:
        logger.error("💥 Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
