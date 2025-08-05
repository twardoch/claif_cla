---
# this_file: src_docs/md/tools/strategies.md
title: Chapter 5 - Tool Approval Strategies
description: Security-focused tool usage control with 8+ built-in approval strategies
---

# Chapter 5: Tool Approval Strategies

Tool approval strategies provide fine-grained security control over MCP (Model Context Protocol) tool usage in claif_cla. This chapter covers all available strategies and how to implement custom approval logic.

## Overview

Tool approval strategies allow you to:
- Control which tools Claude can use
- Implement security policies
- Create risk-based approval systems
- Combine multiple strategies
- Log and monitor tool usage

## Built-in Strategies

### 1. AllowListStrategy
Only allows explicitly permitted tools.

```python
from claif_cla.approval import AllowListStrategy

strategy = AllowListStrategy([
    "read_file",
    "search_files", 
    "list_directory"
])
```

### 2. DenyListStrategy
Blocks specific dangerous tools.

```python
from claif_cla.approval import DenyListStrategy

strategy = DenyListStrategy([
    "delete_file",
    "execute_command",
    "network_request"
])
```

### 3. PatternStrategy
Uses regex patterns for approval.

```python
from claif_cla.approval import PatternStrategy

strategy = PatternStrategy([
    r"read_.*",     # Allow all read operations
    r"search_.*",   # Allow all search operations
    r"list_.*"      # Allow all list operations
])
```

### 4. ThresholdStrategy
Approves based on risk scores.

```python
from claif_cla.approval import ThresholdStrategy

strategy = ThresholdStrategy(
    max_risk=5,  # Allow tools with risk <= 5
    risk_map={
        "read_file": 2,
        "write_file": 7,
        "delete_file": 9,
        "execute_command": 10
    }
)
```

## Custom Strategies

Create custom approval logic by extending the base strategy class:

```python
from claif_cla.approval import ApprovalStrategy

class TimeBasedStrategy(ApprovalStrategy):
    """Only allow certain tools during business hours"""
    
    def should_approve(self, tool_name: str, metadata: dict) -> bool:
        from datetime import datetime
        
        current_hour = datetime.now().hour
        
        # High-risk tools only during business hours
        high_risk_tools = ["delete_file", "execute_command"]
        
        if tool_name in high_risk_tools:
            return 9 <= current_hour <= 17  # 9 AM to 5 PM
        
        return True  # Allow other tools anytime
```

## Strategy Composition

Combine multiple strategies for sophisticated control:

```python
from claif_cla.approval import CompositeStrategy

# Require ALL strategies to approve
strict_strategy = CompositeStrategy([
    AllowListStrategy(["read_file", "search_files"]),
    ThresholdStrategy(max_risk=3),
    TimeBasedStrategy()
], mode="all")

# Require ANY strategy to approve  
permissive_strategy = CompositeStrategy([
    AllowListStrategy(["safe_tool"]),
    PatternStrategy([r"read_.*"])
], mode="any")
```

For complete implementation details, see the [Built-in Strategies](builtin.md) and [Custom Strategies](custom.md) sections.