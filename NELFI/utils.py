import re
from typing import List, Dict, Any
from langchain_core.messages import AIMessage

def ensure_proper_punctuation(text: str) -> str:
    if not text:
        return text
    
    text = text.strip()
    
    if text and text[-1] in {'.', '!', '?', ':', ';'}:
        return text
    
    if text and text[-1] in {'"', "'", ')', ']', '}'}:
        if len(text) > 1 and text[-2] in {'.', '!', '?'}:
            return text
    
    lines = text.split('\n')
    last_line = lines[-1].strip()
    
    if last_line and len(last_line.split()) > 3:
        if not last_line.startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.')):
            text = text + '.'
    
    return text

def extract_sources_from_response(response_text: str) -> List[Dict[str, str]]:
    sources = []
    source_patterns = [
        r'\[Source:\s*([^,]+),\s*Page:\s*([^\]]+)\]',
        r'Source:\s*([^,]+),\s*Page:\s*([^\s\]]+)',
        r'\(Source:\s*([^,]+),\s*Page:\s*([^\)]+)\)'
    ]
    
    for pattern in source_patterns:
        matches = re.finditer(pattern, response_text)
        for match in matches:
            source = match.group(1).strip()
            page = match.group(2).strip()
            
            if 'data/' in source:
                source = source.split('data/')[-1]
            
            source_entry = {
                "source": source,
                "page": page,
                "citation": match.group(0)
            }
            
            if not any(s['source'] == source_entry['source'] and 
                      s['page'] == source_entry['page'] for s in sources):
                sources.append(source_entry)
    
    return sources

def clean_response_text(response_text: str) -> str:
    if not response_text:
        return response_text
    
    response_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', response_text)
    response_text = re.sub(r'([.!?])([A-Z])', r'\1 \2', response_text)
    response_text = re.sub(r'\n\s*[-•*]\s*', '\n• ', response_text)
    
    return response_text.strip()

def extract_content_from_ai_message(message) -> str:
    if isinstance(message.content, str):
        return message.content
    elif isinstance(message.content, list):
        content_parts = []
        for item in message.content:
            if hasattr(item, 'text'):
                content_parts.append(item.text)
            elif isinstance(item, dict) and 'text' in item:
                content_parts.append(item['text'])
            elif isinstance(item, str):
                content_parts.append(item)
        return " ".join(content_parts)
    elif hasattr(message, 'content'):
        return str(message.content)
    else:
        return "I couldn't generate a response. Please try again."

def check_if_retrieval_was_used(result) -> bool:
    for message in result["messages"]:
        if isinstance(message, AIMessage):
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if isinstance(tool_call, dict):
                        if tool_call.get('name') == 'retrieve_nelfund_info':
                            return True
                    elif hasattr(tool_call, 'name'):
                        if tool_call.name == 'retrieve_nelfund_info':
                            return True
    return False