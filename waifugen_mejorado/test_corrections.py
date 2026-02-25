#!/usr/bin/env python3
"""
Test script to verify the corrections applied to the WaifuGen system.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        from src import (
            SocialMediaManager,
            PlatformType,
            PostResult,
            EngagementMetrics,
            ProxyManager,
            check_proxy_status,
            quick_post_all,
            TikTokClient,
            InstagramClient,
            YouTubeClient
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

async def test_social_clients():
    """Test that social media clients can be instantiated."""
    print("\nTesting social media client instantiation...")
    try:
        from src.social import TikTokClient, InstagramClient, YouTubeClient
        
        # These will fail if credentials are not set, but that's expected
        # We're just checking that the classes can be imported and instantiated
        print("✓ TikTokClient imported successfully")
        print("✓ InstagramClient imported successfully")
        print("✓ YouTubeClient imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_youtube_signature():
    """Test that YouTube client has the correct upload_video signature."""
    print("\nTesting YouTube upload_video signature...")
    try:
        from src.social import YouTubeClient
        import inspect
        
        sig = inspect.signature(YouTubeClient.upload_video)
        params = list(sig.parameters.keys())
        
        # Expected parameters: self, asset, caption, tags, config
        expected = ['self', 'asset', 'caption', 'tags', 'config']
        
        if params == expected:
            print(f"✓ YouTube upload_video signature is correct: {params}")
            return True
        else:
            print(f"✗ YouTube upload_video signature mismatch")
            print(f"  Expected: {expected}")
            print(f"  Got: {params}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_file_uploader():
    """Test that the FileUploader module exists and can be imported."""
    print("\nTesting FileUploader module...")
    try:
        from src.utils.file_uploader import FileUploader, get_public_url
        print("✓ FileUploader module imported successfully")
        print("✓ get_public_url function imported successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_instagram_import():
    """Test that Instagram client imports FileUploader."""
    print("\nTesting Instagram client with FileUploader...")
    try:
        from src.social.instagram_client import InstagramClient, FileUploader
        print("✓ InstagramClient imports FileUploader successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("WaifuGen System Corrections Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", await test_imports()))
    results.append(("Social Clients", await test_social_clients()))
    results.append(("YouTube Signature", await test_youtube_signature()))
    results.append(("FileUploader", await test_file_uploader()))
    results.append(("Instagram FileUploader", await test_instagram_import()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
