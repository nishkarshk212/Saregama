#!/usr/bin/env python3
"""
Diagnostic script to check why bot is not responding or sending logs
Run this on your server to diagnose issues.
"""

import asyncio
import sys
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration from .env
API_ID = 33830507
API_HASH = "54e1e0d86c6c2768b65dc945bb2096c7"
BOT_TOKEN = "8775908280:AAGoWZqbEOn_2vO4YXYCuhxCxf7VHNLqp1Y"
MONGO_DB_URI = "mongodb+srv://nishkarshk46:Nishkarsh123@shishimanu.toei5c.mongodb.net/?appName=Shishimanu"
LOGGER_ID = -1003757375746

async def diagnose():
    print("=" * 60)
    print("LILY MUSIC BOT - DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Test 1: MongoDB Connection
    print("\n[1/5] Testing MongoDB connection...")
    try:
        client = AsyncIOMotorClient(MONGO_DB_URI)
        db = client["AnnieXMedia"]
        await client.admin.command('ping')
        print("✅ MongoDB connected successfully")
        
        # Check logging setting
        onoffdb = db["onoff"]
        log_setting = await onoffdb.find_one({"on_off": 2})
        if log_setting:
            print(f"✅ Logging setting found: {log_setting}")
            print("   → Logging is ENABLED in database")
        else:
            print("❌ Logging setting NOT FOUND in database")
            print("   → Run enable_logging.py to fix this")
            
        client.close()
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    
    # Test 2: Bot Authentication
    print("\n[2/5] Testing bot authentication...")
    try:
        app = Client("diagnostic_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
        await app.start()
        bot_info = await app.get_me()
        print(f"✅ Bot authenticated: {bot_info.first_name} (@{bot_info.username})")
        await app.stop()
    except Exception as e:
        print(f"❌ Bot authentication failed: {e}")
        return False
    
    # Test 3: LOGGER_ID Chat Access
    print("\n[3/5] Testing LOGGER_ID access...")
    try:
        app = Client("diag_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
        await app.start()
        
        chat = await app.get_chat(LOGGER_ID)
        print(f"✅ LOGGER_ID accessible: {chat.title}")
        print(f"   Chat Type: {chat.type}")
        
        # Try to send a test message
        try:
            await app.send_message(
                LOGGER_ID,
                "<b>🔧 Diagnostic Test</b>\n\nThis is a test message from the diagnostic tool.\nIf you see this, logging is working correctly!",
            )
            print("✅ Successfully sent test message to LOGGER_ID")
        except Exception as e:
            print(f"❌ Failed to send message to LOGGER_ID: {e}")
            print("   → Make sure bot is admin in the logger group/channel")
        
        await app.stop()
    except Exception as e:
        print(f"❌ Cannot access LOGGER_ID: {e}")
        print(f"   → Current LOGGER_ID: {LOGGER_ID}")
        print("   → Check if the ID is correct and bot is admin there")
    
    # Test 4: File Checks
    print("\n[4/5] Checking configuration files...")
    import os
    if os.path.exists(".env"):
        print("✅ .env file exists")
    else:
        print("❌ .env file missing!")
    
    if os.path.exists("AnnieXMedia"):
        print("✅ AnnieXMedia directory exists")
    else:
        print("❌ AnnieXMedia directory missing!")
    
    # Test 5: Network Connectivity
    print("\n[5/5] Testing network connectivity...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.telegram.org", timeout=5) as resp:
                if resp.status == 200:
                    print("✅ Telegram API accessible")
                else:
                    print(f"⚠️  Telegram API returned status: {resp.status}")
    except Exception as e:
        print(f"❌ Network connectivity issue: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print("\nRECOMMENDATIONS:")
    print("1. If logging setting not found → Run: python3 enable_logging.py")
    print("2. If LOGGER_ID access failed → Add bot as admin to your log group")
    print("3. Restart bot after fixes: systemctl restart lily-music")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(diagnose())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
