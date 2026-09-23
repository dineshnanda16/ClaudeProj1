"""
Test Cohere medication extraction with proper JSON parsing.
"""
import os
from dotenv import load_dotenv
import cohere
import json

load_dotenv()

print('Testing Cohere Medication Extraction')
print('=' * 50)

api_key = os.getenv('COHERE_API_KEY')
model = os.getenv('LLM_MODEL')

# Sample medical text
sample_text = """
PRESCRIPTION

Medications:
1. Metformin 500 mg tablet. Take one tablet twice daily after meals.
2. Atorvastatin 20 mg tablet. Take one tablet at night.
3. Aspirin 75 mg once daily.
"""

# Build extraction prompt (simplified version)
prompt = f"""You are a medical information extraction system. Extract medication information from this document.

Return your response as JSON with this structure:
{{
  "medications": [
    {{
      "medication_name": "...",
      "strength": "...",
      "frequency": "...",
      "instructions": "...",
      "evidence_text": "..."
    }}
  ]
}}

Document text:
{sample_text}

Extract medications now:"""

try:
    client = cohere.ClientV2(api_key=api_key)
    print(f'Using model: {model}')
    print('Sending medication extraction request...')

    response = client.chat(
        model=model,
        messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ],
        temperature=0.0
    )

    print('Response received')

    # Extract content
    content = response.message.content[0].text
    print(f'Content length: {len(content)} characters')
    print('')
    print('Raw response (first 500 chars):')
    print(content[:500])
    print('')

    # Try to parse JSON
    original_content = content
    if '```json' in content:
        json_start = content.find('```json') + 7
        json_end = content.find('```', json_start)
        content = content[json_start:json_end].strip()
        print('Extracted JSON from markdown blocks')
    elif '```' in content:
        json_start = content.find('```') + 3
        json_end = content.find('```', json_start)
        content = content[json_start:json_end].strip()
        print('Extracted content from code blocks')

    print('')
    print('Parsing JSON...')
    data = json.loads(content)

    print(f'Medications found: {len(data.get("medications", []))}')
    print('')

    for idx, med in enumerate(data.get('medications', []), 1):
        print(f'{idx}. {med.get("medication_name")}')
        print(f'   Strength: {med.get("strength", "N/A")}')
        print(f'   Frequency: {med.get("frequency", "N/A")}')
        print(f'   Instructions: {med.get("instructions", "N/A")}')

    print('')
    print('SUCCESS: Medication extraction works!')

except json.JSONDecodeError as e:
    print(f'JSON Parse Error: {e}')
    print(f'Content to parse: {content[:200]}...')
    print('')
    print('Full original response:')
    print(original_content)
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
