#!/usr/bin/env python3
"""
Enable logging by default for Lily Music Bot
This script ensures that logging (setting ID 2) is turned on in the database.
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Database configuration
MONGO_DB_URI = "mongodb+srv://nishkarshk46:Nishkarsh123@shishimanu.toei5c.mongodb.net/?appName=Shishimanu"
DB_NAME = "AnnieXMedia"

async def enable_logging():
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGO_DB_URI)
        db = client[DB_NAME]
        onoffdb = db["onoff"]
        
        # Check current state
        print("Checking current logging state...")
        current = await onoffdb.find_one({"on_off": 2})
        
        if current:
            print(f"Current state: {current}")
        else:
            print("No record found for setting ID 2")
        
        # Enable logging (ID 2)
        print("Enabling logging...")
        result = await onoffdb.update_one(
            {"on_off": 2},
            {"$set": {"on_off": 2}},
            upsert=True
        )
        
        if result.modified_count or result.upserted_id:
            print("✅ Logging enabled successfully!")
        else:
            print("⚠️  No changes made (already enabled?)")
        
        # Verify
        print("Verifying...")
        verify = await onoffdb.find_one({"on_off": 2})
        print(f"Verified state: {verify}")
        
        client.close()
        print("\nDone!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(enable_logging())
