# LangGraph Background Run API - Implementation Templates

**Date:** 2025-08-07  
**Phase:** Implementation Templates  
**Based on:** LANGGRAPH_BACKGROUND_RUN_API_RESEARCH.md

## Implementation Templates

### 1. Result Retrieval Service

```python
# src/services/run_result_retriever.py

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod

from langgraph_sdk import get_client
from langgraph_sdk.schema import StreamPart

logger = logging.getLogger(__name__)

class ResultRetrievalError(Exception):
    """Raised when result retrieval fails"""
    pass

class ResultRetrievalStrategy(ABC):
    """Abstract base class for result retrieval strategies"""
    
    @abstractmethod
    async def retrieve(self, client, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Retrieve results using this strategy"""
        pass
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging"""
        pass

class StreamResultStrategy(ResultRetrievalStrategy):
    """Retrieve results using stream API"""
    
    @property
    def name(self) -> str:
        return "stream_values"
        
    async def retrieve(self, client, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Retrieve results via streaming API"""
        logger.info(f"Attempting stream result retrieval for run {run_id}")
        
        result = {}
        message_count = 0
        
        try:
            async for chunk in client.runs.stream(
                thread_id=thread_id,
                run_id=run_id,
                stream_mode="values"  # Get final values
            ):
                message_count += 1
                if chunk.event == "values" and chunk.data:
                    result.update(chunk.data)
                    logger.debug(f"Stream chunk received: {chunk.event}")
                    
        except Exception as e:
            logger.warning(f"Stream retrieval failed after {message_count} messages: {e}")
            raise ResultRetrievalError(f"Stream API failed: {e}")
            
        if not result:
            raise ResultRetrievalError("Stream returned no data")
            
        logger.info(f"Stream retrieval successful: {len(result)} result fields")
        return result

class ThreadStateStrategy(ResultRetrievalStrategy):
    """Retrieve results using thread state API"""
    
    @property
    def name(self) -> str:
        return "thread_state"
        
    async def retrieve(self, client, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Retrieve results via thread state API"""
        logger.info(f"Attempting thread state retrieval for run {run_id}")
        
        try:
            # Get the current thread state
            state = await client.threads.get_state(thread_id)
            
            if not state or not hasattr(state, 'values'):
                raise ResultRetrievalError("Thread state has no values")
                
            result = state.values
            if not result:
                raise ResultRetrievalError("Thread state values are empty")
                
            logger.info(f"Thread state retrieval successful: {len(result)} result fields")
            return result
            
        except Exception as e:
            logger.warning(f"Thread state retrieval failed: {e}")
            raise ResultRetrievalError(f"Thread state API failed: {e}")

class JoinStreamStrategy(ResultRetrievalStrategy):
    """Retrieve results using join stream API"""
    
    @property
    def name(self) -> str:
        return "join_stream"
        
    async def retrieve(self, client, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Retrieve results via join stream API"""
        logger.info(f"Attempting join stream retrieval for run {run_id}")
        
        result = {}
        timeout_seconds = 10  # Prevent hanging
        
        try:
            async with asyncio.timeout(timeout_seconds):
                async for chunk in client.runs.join_stream(
                    thread_id=thread_id,
                    run_id=run_id,
                    stream_mode="values"
                ):
                    if chunk.event == "values" and chunk.data:
                        result.update(chunk.data)
                        break  # Get the latest values and exit
                        
        except asyncio.TimeoutError:
            raise ResultRetrievalError(f"Join stream timed out after {timeout_seconds}s")
        except Exception as e:
            logger.warning(f"Join stream retrieval failed: {e}")
            raise ResultRetrievalError(f"Join stream API failed: {e}")
            
        if not result:
            raise ResultRetrievalError("Join stream returned no data")
            
        logger.info(f"Join stream retrieval successful: {len(result)} result fields")
        return result

class RunResultRetriever:
    """Main service for retrieving run results with fallback strategies"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.client = get_client(url=base_url, api_key=api_key)
        
        # Define strategy hierarchy (primary -> fallback)
        self.strategies: List[ResultRetrievalStrategy] = [
            StreamResultStrategy(),
            ThreadStateStrategy(),
            JoinStreamStrategy(),
        ]
        
    async def get_result(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """
        Retrieve run results using fallback strategy pattern
        
        Args:
            thread_id: The thread ID
            run_id: The run ID
            
        Returns:
            Dict containing the run results
            
        Raises:
            ResultRetrievalError: If all strategies fail
        """
        errors = []
        
        for strategy in self.strategies:
            try:
                logger.info(f"Trying result retrieval strategy: {strategy.name}")
                start_time = datetime.now()
                
                result = await strategy.retrieve(self.client, thread_id, run_id)
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Strategy {strategy.name} succeeded in {duration:.2f}s")
                
                # Add metadata to result
                result["_retrieval_metadata"] = {
                    "strategy_used": strategy.name,
                    "retrieval_duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                return result
                
            except ResultRetrievalError as e:
                error_msg = f"Strategy {strategy.name} failed: {e}"
                errors.append(error_msg)
                logger.warning(error_msg)
                continue
                
        # All strategies failed
        all_errors = "; ".join(errors)
        raise ResultRetrievalError(f"All result retrieval strategies failed: {all_errors}")

    async def get_result_with_timeout(
        self, 
        thread_id: str, 
        run_id: str, 
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Get results with overall timeout"""
        try:
            async with asyncio.timeout(timeout_seconds):
                return await self.get_result(thread_id, run_id)
        except asyncio.TimeoutError:
            raise ResultRetrievalError(f"Result retrieval timed out after {timeout_seconds}s")
```

### 2. Enhanced Polling Service

```python
# src/services/enhanced_background_run_poller.py

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum

from langgraph_sdk import get_client
from langgraph_sdk.schema import RunStatus
from .run_result_retriever import RunResultRetriever, ResultRetrievalError

logger = logging.getLogger(__name__)

class PollingResult(Enum):
    """Polling result types"""
    SUCCESS_WITH_RESULTS = "success_with_results"
    SUCCESS_NO_RESULTS = "success_no_results" 
    ERROR = "error"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"

class EnhancedBackgroundRunPoller:
    """
    Enhanced background run poller with separate result retrieval
    
    Follows SOLID principles:
    - Single Responsibility: Status polling vs result retrieval
    - Open/Closed: Extensible for new retrieval strategies
    - Dependency Inversion: Abstract result retrieval interface
    """
    
    def __init__(
        self, 
        base_url: str, 
        api_key: Optional[str] = None,
        poll_interval: float = 10.0,
        max_poll_time: float = 600.0  # 10 minutes default
    ):
        self.client = get_client(url=base_url, api_key=api_key)
        self.result_retriever = RunResultRetriever(base_url, api_key)
        self.poll_interval = poll_interval
        self.max_poll_time = max_poll_time
        
    async def poll_status_only(self, thread_id: str, run_id: str) -> RunStatus:
        """
        Poll for run status only (existing functionality)
        
        This method maintains the existing behavior and can be used
        when only status information is needed.
        """
        try:
            run = await self.client.runs.get(thread_id=thread_id, run_id=run_id)
            return run.status
        except Exception as e:
            logger.error(f"Status polling failed for run {run_id}: {e}")
            raise

    async def poll_until_complete_with_results(
        self, 
        thread_id: str, 
        run_id: str
    ) -> Dict[str, Any]:
        """
        Complete polling workflow: status + results
        
        Phase 1: Poll until completion (existing logic)
        Phase 2: Retrieve results (new logic)
        
        Returns comprehensive result with status and content
        """
        start_time = datetime.now()
        poll_count = 0
        
        logger.info(f"Starting enhanced polling for run {run_id}")
        
        # Phase 1: Poll for completion
        try:
            while True:
                poll_count += 1
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if elapsed > self.max_poll_time:
                    return self._create_timeout_result(thread_id, run_id, poll_count, elapsed)
                
                logger.debug(f"Poll #{poll_count} for run {run_id} (elapsed: {elapsed:.1f}s)")
                
                status = await self.poll_status_only(thread_id, run_id)
                
                if status in ["success", "error", "timeout", "interrupted"]:
                    logger.info(f"Run {run_id} completed with status: {status} after {poll_count} polls")
                    break
                    
                await asyncio.sleep(self.poll_interval)
                
        except Exception as e:
            return self._create_error_result(thread_id, run_id, poll_count, str(e))
        
        # Phase 2: Handle completion based on status
        completion_time = (datetime.now() - start_time).total_seconds()
        
        if status == "success":
            return await self._handle_success_result(
                thread_id, run_id, poll_count, completion_time
            )
        else:
            return self._create_non_success_result(
                thread_id, run_id, status, poll_count, completion_time
            )

    async def _handle_success_result(
        self, 
        thread_id: str, 
        run_id: str, 
        poll_count: int, 
        completion_time: float
    ) -> Dict[str, Any]:
        """Handle successful run completion with result retrieval"""
        
        try:
            logger.info(f"Retrieving results for successful run {run_id}")
            result_content = await self.result_retriever.get_result_with_timeout(
                thread_id, run_id, timeout_seconds=30.0
            )
            
            return {
                "polling_result": PollingResult.SUCCESS_WITH_RESULTS.value,
                "status": "success",
                "run_id": run_id,
                "thread_id": thread_id,
                "result": result_content,
                "polling_metadata": {
                    "poll_count": poll_count,
                    "completion_time_seconds": completion_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except ResultRetrievalError as e:
            logger.error(f"Result retrieval failed for run {run_id}: {e}")
            
            # Return success status but indicate result retrieval failure
            return {
                "polling_result": PollingResult.SUCCESS_NO_RESULTS.value,
                "status": "success", 
                "run_id": run_id,
                "thread_id": thread_id,
                "error": f"Result retrieval failed: {e}",
                "polling_metadata": {
                    "poll_count": poll_count,
                    "completion_time_seconds": completion_time,
                    "result_retrieval_error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _create_non_success_result(
        self, 
        thread_id: str, 
        run_id: str, 
        status: str, 
        poll_count: int, 
        completion_time: float
    ) -> Dict[str, Any]:
        """Create result for non-success completion"""
        
        polling_result_map = {
            "error": PollingResult.ERROR,
            "timeout": PollingResult.TIMEOUT, 
            "interrupted": PollingResult.INTERRUPTED
        }
        
        return {
            "polling_result": polling_result_map.get(status, PollingResult.ERROR).value,
            "status": status,
            "run_id": run_id,
            "thread_id": thread_id,
            "polling_metadata": {
                "poll_count": poll_count,
                "completion_time_seconds": completion_time,
                "timestamp": datetime.now().isoformat()
            }
        }

    def _create_timeout_result(
        self, 
        thread_id: str, 
        run_id: str, 
        poll_count: int, 
        elapsed: float
    ) -> Dict[str, Any]:
        """Create result for polling timeout"""
        
        return {
            "polling_result": PollingResult.TIMEOUT.value,
            "status": "polling_timeout",
            "run_id": run_id,
            "thread_id": thread_id,
            "error": f"Polling timed out after {elapsed:.1f}s ({poll_count} polls)",
            "polling_metadata": {
                "poll_count": poll_count,
                "elapsed_seconds": elapsed,
                "max_poll_time": self.max_poll_time,
                "timestamp": datetime.now().isoformat()
            }
        }

    def _create_error_result(
        self, 
        thread_id: str, 
        run_id: str, 
        poll_count: int, 
        error: str
    ) -> Dict[str, Any]:
        """Create result for polling error"""
        
        return {
            "polling_result": PollingResult.ERROR.value,
            "status": "polling_error",
            "run_id": run_id,
            "thread_id": thread_id,
            "error": error,
            "polling_metadata": {
                "poll_count": poll_count,
                "timestamp": datetime.now().isoformat()
            }
        }

# Backward compatibility wrapper
class BackgroundRunPoller(EnhancedBackgroundRunPoller):
    """Backward compatibility wrapper maintaining existing interface"""
    
    async def poll_until_complete(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Maintain existing interface while adding new functionality"""
        return await self.poll_until_complete_with_results(thread_id, run_id)
```

### 3. Integration Example

```python
# src/examples/enhanced_polling_example.py

import asyncio
import logging
from typing import Dict, Any

from src.services.enhanced_background_run_poller import EnhancedBackgroundRunPoller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demonstrate_enhanced_polling():
    """Demonstrate the enhanced polling with result retrieval"""
    
    # Test data from logs
    thread_id = "e8e9d596-25f6-4d72-af3d-ff13c901aa8f"
    run_id = "1f073d12-1030-6677-9a30-d739d108e227"
    
    # Initialize enhanced poller
    poller = EnhancedBackgroundRunPoller(
        base_url="http://localhost:8124",
        poll_interval=5.0,  # Poll every 5 seconds
        max_poll_time=300.0  # 5 minute timeout
    )
    
    logger.info("🚀 Starting enhanced background run polling demonstration")
    
    try:
        # Complete polling workflow with results
        result = await poller.poll_until_complete_with_results(thread_id, run_id)
        
        # Process results
        polling_result = result.get("polling_result")
        status = result.get("status")
        
        if polling_result == "success_with_results":
            logger.info("✅ Polling successful with results retrieved!")
            
            # Extract result content
            result_content = result.get("result", {})
            retrieval_metadata = result_content.get("_retrieval_metadata", {})
            
            logger.info(f"📊 Result retrieval strategy: {retrieval_metadata.get('strategy_used')}")
            logger.info(f"⏱️  Retrieval duration: {retrieval_metadata.get('retrieval_duration_seconds'):.2f}s")
            logger.info(f"📋 Result keys: {list(result_content.keys())}")
            
            # Log specific trading analysis results if available
            if "trading_signal" in result_content:
                logger.info(f"📈 Trading signal: {result_content['trading_signal']}")
            if "analysis_summary" in result_content:
                logger.info(f"📝 Analysis summary available: {len(result_content['analysis_summary'])} characters")
                
        elif polling_result == "success_no_results":
            logger.warning("⚠️  Polling successful but result retrieval failed")
            logger.warning(f"   Error: {result.get('error')}")
            
        else:
            logger.error(f"❌ Polling failed: {polling_result}")
            logger.error(f"   Status: {status}")
            if "error" in result:
                logger.error(f"   Error: {result['error']}")
        
        # Log polling metadata
        metadata = result.get("polling_metadata", {})
        if metadata:
            logger.info(f"📊 Polling metadata:")
            logger.info(f"   Polls: {metadata.get('poll_count')}")
            logger.info(f"   Duration: {metadata.get('completion_time_seconds', 0):.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Enhanced polling failed: {e}")
        raise

async def demonstrate_backward_compatibility():
    """Demonstrate that existing code continues to work"""
    
    from src.services.enhanced_background_run_poller import BackgroundRunPoller
    
    # Existing interface still works
    poller = BackgroundRunPoller(base_url="http://localhost:8124")
    
    result = await poller.poll_until_complete(
        thread_id="e8e9d596-25f6-4d72-af3d-ff13c901aa8f",
        run_id="1f073d12-1030-6677-9a30-d739d108e227"
    )
    
    logger.info("✅ Backward compatibility maintained")
    return result

if __name__ == "__main__":
    # Run demonstrations
    asyncio.run(demonstrate_enhanced_polling())
    asyncio.run(demonstrate_backward_compatibility())
```

## Usage Examples

### Quick Start - Enhanced Polling

```python
from src.services.enhanced_background_run_poller import EnhancedBackgroundRunPoller

# Initialize with your LangGraph server
poller = EnhancedBackgroundRunPoller(
    base_url="http://your-langgraph-server:8124",
    api_key="your-api-key"  # Optional
)

# Poll with automatic result retrieval
result = await poller.poll_until_complete_with_results(thread_id, run_id)

if result["polling_result"] == "success_with_results":
    # Success! Results are available
    analysis_results = result["result"]
    print(f"Trading analysis completed: {analysis_results}")
else:
    # Handle other cases
    print(f"Polling result: {result['polling_result']}")
    if "error" in result:
        print(f"Error: {result['error']}")
```

### Direct Result Retrieval

```python
from src.services.run_result_retriever import RunResultRetriever

# Just retrieve results (if you know the run is complete)
retriever = RunResultRetriever(base_url="http://your-langgraph-server:8124")

try:
    results = await retriever.get_result(thread_id, run_id)
    print(f"Results retrieved using strategy: {results['_retrieval_metadata']['strategy_used']}")
except ResultRetrievalError as e:
    print(f"Failed to retrieve results: {e}")
```

This completes the implementation templates for the enhanced LangGraph Background Run API integration.