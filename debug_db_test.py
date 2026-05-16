#!/usr/bin/env python3
"""Debug script to test database connection issues."""

import asyncio
import json
import time
from pathlib import Path
from sqlalchemy import text
from src.core.database import AsyncSessionLocal, engine

def _debug_log(message: str, data: dict, hypothesis_id: str):
    try:
        log_entry = {
            "sessionId": "25bd74",
            "id": f"log_{int(time.time() * 1000)}_{hypothesis_id}",
            "timestamp": int(time.time() * 1000),
            "location": "debug_db_test.py",
            "message": message,
            "data": data,
            "runId": "initial",
            "hypothesisId": hypothesis_id
        }
        Path("debug-25bd74.log").open("a").write(json.dumps(log_entry) + "\n")
    except:
        pass

async def test_basic_connection():
    """Test basic database operations that are failing."""
    
    # #region agent log
    _debug_log("Starting DB test", {}, "C")
    # #endregion
    
    try:
        # Test 1: Simple query
        # #region agent log
        _debug_log("Test 1: Creating session for simple query", {}, "C")
        # #endregion
        
        async with AsyncSessionLocal() as session:
            # #region agent log
            _debug_log("Session created, executing SELECT 1", {}, "C")
            # #endregion
            
            result = await session.execute(text("SELECT 1 as test"))
            value = result.scalar()
            
            # #region agent log
            _debug_log("SELECT 1 completed", {"result": value}, "C")
            # #endregion
        
        # #region agent log
        _debug_log("Test 1 completed successfully", {}, "C")
        # #endregion
        
    except Exception as e:
        # #region agent log
        _debug_log("Test 1 failed", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "C")
        # #endregion
        return
    
    try:
        # Test 2: Pool status check
        # #region agent log
        _debug_log("Test 2: Checking pool status", {
            "pool_size": getattr(engine.pool, 'size', lambda: "unknown")(),
            "checked_in": getattr(engine.pool, 'checkedin', lambda: "unknown")(),
            "checked_out": getattr(engine.pool, 'checkedout', lambda: "unknown")(),
            "overflow": getattr(engine.pool, 'overflow', lambda: "unknown")()
        }, "A")
        # #endregion
        
    except Exception as e:
        # #region agent log
        _debug_log("Test 2 failed", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "A")
        # #endregion
    
    try:
        # Test 3: Transaction with timeout
        # #region agent log
        _debug_log("Test 3: Starting transaction test", {}, "D")
        # #endregion
        
        timeout_start = time.time()
        async with engine.begin() as conn:
            # #region agent log
            _debug_log("Transaction started", {"elapsed": time.time() - timeout_start}, "D")
            # #endregion
            
            result = await conn.execute(text("SELECT current_database(), version()"))
            db_info = result.fetchone()
            
            # #region agent log
            _debug_log("Transaction query completed", {
                "database": db_info[0] if db_info else None,
                "version": db_info[1][:50] if db_info and db_info[1] else None,
                "elapsed": time.time() - timeout_start
            }, "D")
            # #endregion
        
        # #region agent log
        _debug_log("Test 3 completed successfully", {"total_elapsed": time.time() - timeout_start}, "D")
        # #endregion
        
    except Exception as e:
        # #region agent log
        _debug_log("Test 3 failed", {
            "error": str(e),
            "error_type": type(e).__name__,
            "elapsed": time.time() - timeout_start
        }, "D")
        # #endregion

if __name__ == "__main__":
    # #region agent log
    _debug_log("Debug script started", {}, "C")
    # #endregion
    
    asyncio.run(test_basic_connection())
    
    # #region agent log
    _debug_log("Debug script completed", {}, "C")
    # #endregion