import inspect
from typing import Callable, Any, get_type_hints

def get_type_name(t: Any) -> str:
    if t == int:
        return "integer"
    elif t == float:
        return "number"
    elif t == bool:
        return "boolean"
    else:
        return "string"

def function_to_json_schema(func: Callable) -> dict:
    """Convert a Python function to an OpenAI/Groq compatible tool JSON schema."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
            
        param_type = type_hints.get(param_name, str)
        schema_type = get_type_name(param_type)
        
        properties[param_name] = {
            "type": schema_type,
            "description": f"The {param_name} parameter."
        }
        
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
            
    # Use the first line of the docstring as the description, or a default
    docstring = inspect.getdoc(func)
    description = docstring.split("\n")[0] if docstring else f"Call the {func.__name__} function."
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
