## LangGraph Trace Analysis Guide

**Role:** LangGraph Smith Trace Analyst Expert
**Purpose:** Provide a detailed, step-by-step guide for analysts to accurately analyze a LangGraph trace. This includes full breakdowns of graph execution, node sequencing, tool interactions, and message flow.

---

### Step 0: Preparation

* Open the trace in LangGraph Studio or export it in JSON if working offline.
* Set the display mode to **"Chronological Order"** to ensure events are viewed in execution sequence.
* Identify the **initial user input**, assistant message, or trigger signal that initiated the trace.

---

### Step 1: Identify Entry Node

* Locate the **first node** executed in the graph.
* This is typically a Planner, Router, or InputHandler.
* Record:

  * Node Type: e.g., Planner
  * Input: Usually the user's prompt or message
  * Output: A structured plan or the next step in the graph
  * Node ID and Timestamp for traceability

---

### Step 2: Follow Graph Execution Path

For each subsequent node in execution order:

* Note the **Node ID**, Type (LLM, ToolCaller, Router), and Role
* Record the **Input**:

  * Derived from previous node or memory
  * Context objects injected by the runtime
* Analyze the **Output**:

  * JSON, Text, or Tool call
  * Branch taken or next step activated
  * Capture retry or fallback behavior if any
* If the graph forks into multiple paths, document:

  * All active branches
  * Their triggering conditions and any skipped routes

Repeat until you reach the final node.

---

### Step 3: Tool Call Analysis

For each ToolCaller or external call node:

* Record:

  * Tool Name (e.g., get\_stock\_price, fetch\_news)
  * Tool Parameters and Inputs
* Validate Tool Output:

  * Returned schema and format
  * Missing fields (null/undefined)
  * Runtime errors or empty returns
  * Warnings include blocking calls, etc
* Confirm that the **next node** processed tool results correctly:

  * Did it parse expected fields?
  * Was fallback logic triggered unnecessarily?

---

### Step 4: Final Summary Node

* Identify the node responsible for summarizing or finalizing the trace:

  * Often a Debater or Aggregator
* Record:

  * Inputs: all analyst outputs, memory, planner summary
  * Final message or report generated for user/API
* Verify:

  * Output structure is well-formed
  * All required fields and sections are filled

---

### Step 5: Error + Edge Case Review

* Scan for irregularities:

  * Nodes skipped due to conditional routing
  * Unused branches or failed conditions
  * Retry attempts and fallback paths
  * Empty message responses
* Flag cases where tool calls returned but were never consumed

---

### Step 6: Cross-Validation Checklist

* Compare graph path to initial **Planner plan**:

  * Were all planner-selected branches actually followed?
* Ensure:

  * All tool calls are reflected in final user-visible output
  * Memory/context was correctly injected and updated
  * LLM completions respect token limits and output formatting rules

---

### Step 7: Issue Summary and Fix Proposal

* Compile a full list of identified issues:

  * Execution gaps, inefficient branches, tool misuse, empty returns
* For each issue, propose:

  * Fixes (code changes, better defaults, tighter validation)
  * Improvements (planner enhancements, context schema adjustments, robust fallback logic)

---

### Optional: Annotate + Tag for Future Review

* Use Studio annotations to highlight important observations
* Tag trace with identifiers like `#routing-fail`, `#tool-error`, `#planner-mismatch`
* Suggest pull requests or module changes when agent behavior is clearly flawed

---

### Deliverable

Provide a complete report that includes:

* Full node-by-node walkthrough
* Inputs and outputs per node
* Tool behaviors and responses
* Final output and user-facing result
* Summary of all discovered issues with fix suggestions

---

