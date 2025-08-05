---
# this_file: src_docs/md/getting-started/examples.md
title: Basic Examples
description: Practical examples to get you started with claif_cla
---

# Basic Examples

This page provides practical, real-world examples to help you understand how to use claif_cla effectively in various scenarios.

## Code Examples

### Example 1: Code Review Assistant

```python
from claif_cla import ClaudeClient

def code_review_assistant():
    """AI-powered code review helper"""
    client = ClaudeClient()
    
    code_to_review = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    '''
    
    response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert code reviewer. Provide constructive feedback on code quality, performance, and best practices."
            },
            {
                "role": "user", 
                "content": f"Please review this Python code:\n\n```python\n{code_to_review}\n```"
            }
        ],
        temperature=0.3  # Lower temperature for consistent, focused reviews
    )
    
    return response.choices[0].message.content

# Usage
review = code_review_assistant()
print(review)
```

### Example 2: Documentation Generator

```python
from claif_cla import ClaudeClient
import ast
import inspect

class DocGenerator:
    def __init__(self):
        self.client = ClaudeClient()
    
    def generate_docstring(self, function_code: str) -> str:
        """Generate a comprehensive docstring for a function"""
        
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": "Generate comprehensive Python docstrings following Google style guide. Include description, parameters, returns, and examples."
                },
                {
                    "role": "user",
                    "content": f"Generate a docstring for this function:\n\n```python\n{function_code}\n```"
                }
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    
    def document_module(self, module_path: str):
        """Generate documentation for an entire Python module"""
        with open(module_path, 'r') as f:
            source = f.read()
        
        response = self.client.chat.completions.create(
            model="claude-3-opus-20240229",  # Use most capable model
            messages=[
                {
                    "role": "system",
                    "content": "Create comprehensive module documentation including overview, classes, functions, and usage examples."
                },
                {
                    "role": "user",
                    "content": f"Document this Python module:\n\n```python\n{source}\n```"
                }
            ],
            max_tokens=4000
        )
        
        return response.choices[0].message.content

# Usage
doc_gen = DocGenerator()

# Document a specific function
function_code = '''
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
'''

docstring = doc_gen.generate_docstring(function_code)
print(docstring)
```

### Example 3: Smart Code Completion

```python
from claif_cla import ClaudeClient

class CodeCompletion:
    def __init__(self):
        self.client = ClaudeClient()
        self.context = []  # Maintain conversation context
    
    def complete_code(self, partial_code: str, context: str = "") -> str:
        """Complete partial code with AI assistance"""
        
        messages = [
            {
                "role": "system",
                "content": "Complete the given code snippet. Provide only the completion, maintaining the existing style and logic."
            }
        ]
        
        # Add conversation context
        for msg in self.context[-4:]:  # Keep last 4 exchanges
            messages.append(msg)
        
        messages.append({
            "role": "user",
            "content": f"Context: {context}\n\nComplete this code:\n```python\n{partial_code}"
        })
        
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            temperature=0.1,  # Low temperature for deterministic completions
            max_tokens=500
        )
        
        completion = response.choices[0].message.content
        
        # Store in context for next completion
        self.context.extend([
            {"role": "user", "content": partial_code},
            {"role": "assistant", "content": completion}
        ])
        
        return completion

# Usage
completer = CodeCompletion()

partial_code = '''
class DataProcessor:
    def __init__(self, data_source):
        self.data_source = data_source
    
    def process_data(self):
        # TODO: Implement data processing logic
'''

completion = completer.complete_code(
    partial_code, 
    context="Building a data processing pipeline for CSV files"
)
print(completion)
```

## CLI Examples

### Example 4: Automated Code Analysis

```bash
#!/bin/bash
# analyze_project.sh - Automated project analysis script

echo "🔍 Starting project analysis..."

# Analyze Python files for potential issues
find . -name "*.py" -exec claif-cla query \
    "Analyze this Python file for potential issues, security concerns, and improvements: $(cat {})" \
    --model claude-3-5-sonnet-20241022 \
    --max-tokens 1000 \
    --output-file "analysis_$(basename {}).md" \;

# Generate project overview
claif-cla query \
    "Analyze this project structure and provide an overview: $(find . -type f -name '*.py' | head -20 | xargs ls -la)" \
    --model claude-3-opus-20240229 \
    --output-file "project_overview.md"

echo "✅ Analysis complete! Check the generated markdown files."
```

### Example 5: Interactive Code Mentor

```bash
#!/bin/bash
# code_mentor.sh - Interactive coding mentor session

# Create a coding mentor session
SESSION_ID=$(claif-cla session create \
    --template coding \
    --metadata '{"topic": "python", "level": "intermediate"}' \
    --return-id)

echo "💡 Starting coding mentor session: $SESSION_ID"

# Set up the mentor context
claif-cla ask \
    "You are an experienced Python mentor. Help me learn by asking probing questions and providing detailed explanations." \
    --session $SESSION_ID

# Start interactive session
echo "🎓 Coding mentor ready! Type 'exit' to end session."
while true; do
    read -p "Ask your coding question: " question
    if [ "$question" = "exit" ]; then
        break
    fi
    
    claif-cla ask "$question" --session $SESSION_ID --stream
    echo -e "\n"
done

# Export session for review
claif-cla session export $SESSION_ID \
    --format markdown \
    --output "mentor_session_$(date +%Y%m%d).md"

echo "📚 Session exported! Review your learning at mentor_session_$(date +%Y%m%d).md"
```

## Practical Applications

### Example 6: Test Case Generator

```python
from claif_cla import ClaudeClient
import textwrap

class TestGenerator:
    def __init__(self):
        self.client = ClaudeClient()
    
    def generate_tests(self, function_code: str, test_framework: str = "pytest") -> str:
        """Generate comprehensive test cases for a function"""
        
        prompt = textwrap.dedent(f"""
        Generate comprehensive test cases for this function using {test_framework}.
        Include:
        - Normal cases
        - Edge cases 
        - Error cases
        - Boundary conditions
        - Mock any external dependencies
        
        Function to test:
        ```python
        {function_code}
        ```
        """)
        
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a testing expert. Generate thorough {test_framework} test cases with good coverage and clear naming."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def generate_mock_data(self, data_structure: str) -> str:
        """Generate realistic mock data for testing"""
        
        response = self.client.chat.completions.create(
            model="claude-3-haiku-20240307",  # Fast model for data generation
            messages=[
                {
                    "role": "system",
                    "content": "Generate realistic mock data that follows the given structure. Make it varied and representative."
                },
                {
                    "role": "user",
                    "content": f"Generate mock data for: {data_structure}"
                }
            ]
        )
        
        return response.choices[0].message.content

# Usage
test_gen = TestGenerator()

function_to_test = '''
def validate_email(email: str) -> bool:
    """Validate email address format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
'''

tests = test_gen.generate_tests(function_to_test)
print(tests)

# Generate mock data
mock_data = test_gen.generate_mock_data("List of user profiles with name, email, age, and preferences")
print(mock_data)
```

### Example 7: API Client Generator

```python
from claif_cla import ClaudeClient
import json

class APIClientGenerator:
    def __init__(self):
        self.client = ClaudeClient()
    
    def generate_client(self, api_spec: dict) -> str:
        """Generate a Python API client from OpenAPI specification"""
        
        spec_json = json.dumps(api_spec, indent=2)
        
        response = self.client.chat.completions.create(
            model="claude-3-opus-20240229",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a clean, well-documented Python API client from OpenAPI specification. Include error handling, type hints, and async support."
                },
                {
                    "role": "user",
                    "content": f"Generate a Python client for this API:\n\n```json\n{spec_json}\n```"
                }
            ],
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def generate_tests_for_client(self, client_code: str) -> str:
        """Generate tests for the generated API client"""
        
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": "Generate comprehensive pytest tests for this API client. Include mocking of HTTP calls and various response scenarios."
                },
                {
                    "role": "user",
                    "content": f"Generate tests for:\n\n```python\n{client_code}\n```"
                }
            ],
            max_tokens=3000
        )
        
        return response.choices[0].message.content

# Usage
api_generator = APIClientGenerator()

# Example API specification
api_spec = {
    "openapi": "3.0.0",
    "info": {"title": "User API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {"summary": "List users"},
            "post": {"summary": "Create user"}
        },
        "/users/{id}": {
            "get": {"summary": "Get user by ID"},
            "delete": {"summary": "Delete user"}
        }
    }
}

client_code = api_generator.generate_client(api_spec)
print("Generated API Client:")
print(client_code)

tests = api_generator.generate_tests_for_client(client_code)
print("\nGenerated Tests:")
print(tests)
```

## Stream Processing Examples

### Example 8: Real-time Code Review

```python
from claif_cla import ClaudeClient

class StreamingCodeReview:
    def __init__(self):
        self.client = ClaudeClient()
    
    def stream_review(self, code: str):
        """Stream code review feedback in real-time"""
        
        print("🔍 Analyzing code...")
        
        stream = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": "Provide detailed code review feedback. Structure your response with clear sections: Issues, Suggestions, Best Practices, and Overall Assessment."
                },
                {
                    "role": "user",
                    "content": f"Review this code:\n\n```python\n{code}\n```"
                }
            ],
            stream=True,
            temperature=0.3
        )
        
        current_line = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                current_line += content
                
                # Print complete lines for better readability
                if '\n' in current_line:
                    lines = current_line.split('\n')
                    for line in lines[:-1]:
                        print(line)
                    current_line = lines[-1]
        
        # Print any remaining content
        if current_line:
            print(current_line)

# Usage
reviewer = StreamingCodeReview()

code_sample = '''
def process_data(data):
    result = []
    for item in data:
        if item is not None:
            result.append(item * 2)
    return result
'''

reviewer.stream_review(code_sample)
```

### Example 9: Interactive Tutorial Generator

```python
from claif_cla import ClaudeClient

class InteractiveTutorial:
    def __init__(self):
        self.client = ClaudeClient()
        self.conversation = []
    
    def generate_tutorial_step(self, topic: str, step: int, total_steps: int):
        """Generate tutorial content step by step"""
        
        self.conversation.append({
            "role": "user",
            "content": f"Generate step {step} of {total_steps} for a tutorial on '{topic}'. Make it interactive with examples and exercises."
        })
        
        stream = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": "You are an engaging programming tutor. Create interactive tutorials with clear explanations, code examples, and practice exercises."
                }
            ] + self.conversation,
            stream=True,
            temperature=0.4
        )
        
        content = ""
        print(f"\n📚 Step {step}/{total_steps}: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                char = chunk.choices[0].delta.content
                content += char
                print(char, end="", flush=True)
        
        self.conversation.append({
            "role": "assistant",
            "content": content
        })
        
        return content

# Usage
tutorial = InteractiveTutorial()

# Generate a 3-step Python tutorial
topic = "Python list comprehensions"
for step in range(1, 4):
    tutorial.generate_tutorial_step(topic, step, 3)
    
    # Wait for user to continue
    input("\n\nPress Enter to continue to next step...")
```

## Integration Examples

### Example 10: IDE Extension Helper

```python
from claif_cla import ClaudeClient
import os
import subprocess

class IDEHelper:
    def __init__(self):
        self.client = ClaudeClient()
    
    def explain_error(self, error_message: str, code_context: str = "") -> str:
        """Explain compilation/runtime errors with suggestions"""
        
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": "Explain programming errors clearly and provide specific fix suggestions. Be concise but comprehensive."
                },
                {
                    "role": "user",
                    "content": f"Error: {error_message}\n\nCode context:\n{code_context}\n\nExplain what's wrong and how to fix it."
                }
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    
    def suggest_improvements(self, file_path: str) -> str:
        """Analyze a file and suggest improvements"""
        
        with open(file_path, 'r') as f:
            code = f.read()
        
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze code for improvements in performance, readability, maintainability, and best practices."
                },
                {
                    "role": "user",
                    "content": f"Suggest improvements for:\n\n```python\n{code}\n```"
                }
            ],
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def generate_commit_message(self, diff: str) -> str:
        """Generate semantic commit messages from git diff"""
        
        response = self.client.chat.completions.create(
            model="claude-3-haiku-20240307",  # Fast model for simple task
            messages=[
                {
                    "role": "system",
                    "content": "Generate concise, semantic commit messages following conventional commits format. Focus on the 'what' and 'why'."
                },
                {
                    "role": "user",
                    "content": f"Generate commit message for:\n\n```diff\n{diff}\n```"
                }
            ],
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()

# Usage
ide_helper = IDEHelper()

# Explain an error
error = "NameError: name 'varaible' is not defined"
context = "x = 10\nprint(varaible)"
explanation = ide_helper.explain_error(error, context)
print(explanation)

# Get git commit message
try:
    diff = subprocess.check_output(['git', 'diff', '--staged'], text=True)
    if diff:
        commit_msg = ide_helper.generate_commit_message(diff)
        print(f"Suggested commit message: {commit_msg}")
except subprocess.CalledProcessError:
    print("No git repository or staged changes found")
```

## Next Steps

These examples should give you a solid foundation for using claif_cla in real projects. To dive deeper:

1. **[API Reference](../api/openai-compatibility.md)** - Learn all available methods and parameters
2. **[Session Management](../sessions/overview.md)** - Build stateful applications with conversation history
3. **[Tool Approval](../tools/strategies.md)** - Control AI tool usage for security
4. **[Advanced Features](../advanced/caching.md)** - Optimize performance with caching and configuration

## Tips for Success

1. **Start Simple**: Begin with basic queries and gradually add complexity
2. **Use Appropriate Models**: Choose faster models for simple tasks, more capable ones for complex reasoning
3. **Handle Errors**: Always implement proper error handling for production use
4. **Cache Responses**: Use caching for repeated or expensive queries
5. **Monitor Usage**: Track API usage to optimize costs
6. **Test Thoroughly**: AI responses can vary, so test edge cases

Happy coding with claif_cla! 🚀