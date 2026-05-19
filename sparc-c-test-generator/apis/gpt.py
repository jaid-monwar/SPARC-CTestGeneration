import os
import re
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any, List, Optional, Type
from apis.token_calculator import get_token_calculator

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Model mappings for each provider
MODEL_MAPPING = {
    "gpt": "gpt-4.1-2025-04-14",
    "gemini": "gemini-2.5-flash",
    "openrouter": "openai/gpt-4o-mini",  # Default OpenRouter model
    "deepseek": "deepseek-chat",  # DeepSeek chat model
}

# Global provider setting (can be set via set_default_provider)
_default_provider = os.getenv("LLM_PROVIDER", "gpt")


def set_default_provider(provider: str):
    """Set the default LLM provider for all GPT_Connection instances."""
    global _default_provider
    _default_provider = provider.lower()
    os.environ["LLM_PROVIDER"] = _default_provider
    print(f"🔧 Default LLM provider set to: {_default_provider}")


def get_default_provider() -> str:
    """Get the current default LLM provider."""
    return _default_provider


class GPT_Connection:
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize the LLM connection.

        Args:
            model: The model name to use. If not specified, uses the default for the provider.
            provider: Either "gpt" for OpenAI or "gemini" for Google Gemini.
                     If not specified, uses the default provider (set via set_default_provider or LLM_PROVIDER env var).
        """
        # Use default provider if not specified
        self.provider = (provider or _default_provider).lower()

        # Set model based on provider if not specified
        if model is None:
            self.model = MODEL_MAPPING.get(self.provider, MODEL_MAPPING["gpt"])
        else:
            self.model = model
        
        # print(f"🤖 Using model: {self.model}")
        # print(f"🤖 Using provider: {self.provider}")
        # print(f"🤖 Using API key: {OPENROUTER_API_KEY if self.provider == 'openrouter' else OPENAI_API_KEY}")

        self.raw_response_dir = "apis/tmp/raw_response"
        # Ensure the directory exists
        os.makedirs(self.raw_response_dir, exist_ok=True)

        # Initialize the appropriate client
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(self.model)
                self.client = None  # No OpenAI client needed
                print(f"🤖 Using Gemini model: {self.model}")
            except ImportError:
                raise ImportError(
                    "google-generativeai package is required for Gemini support. "
                    "Install it with: pip install google-generativeai"
                )
        elif self.provider == "openrouter":
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY
            )
            self.gemini_model = None
            print(f"🤖 Using OpenRouter model: {self.model}")
        elif self.provider == "deepseek":
            self.client = OpenAI(
                base_url="https://api.deepseek.com",
                api_key=DEEPSEEK_API_KEY
            )
            self.gemini_model = None
            print(f"🤖 Using DeepSeek model: {self.model}")
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.gemini_model = None
            print(f"🤖 Using OpenAI model: {self.model}")

    def _save_raw_response(
        self,
        context: str,
        request_data: dict,
        response_data: dict,
        model_type: str = "chat",
    ):
        """
        Save raw LLM request and response to file for debugging and analysis.

        Args:
            context: Description of what this request is for (e.g., "operation_map_generation", "test_scenarios_validation")
            request_data: The request data sent to the LLM
            response_data: The raw response from the LLM
            model_type: Type of model call ("chat", "embedding", etc.)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
            :-3
        ]  # Include milliseconds
        filename = f"{timestamp}_{context}_{model_type}.json"
        filepath = os.path.join(self.raw_response_dir, filename)

        # Prepare the data to save
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "model_type": model_type,
            "model": self.model,
            "request": request_data,
            "response": response_data,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"📝 Raw response saved: {filename}")
        except Exception as e:
            print(f"Failed to save raw response: {e}")

    def generate_chat_completion(
        self, messages=[], temperature=0, response_model=None, context="unknown", max_tokens=8192
    ):
        # Track input tokens using TokenCalculator
        token_calculator = get_token_calculator()
        input_tokens = token_calculator.track_tokens(messages, context, self.model)
        # print(f"🔢 Input tokens for {context}: {input_tokens:,}")

        # Prepare request data for logging
        request_data = {
            "messages": messages,
            "model": self.model,
            "provider": self.provider,
            "temperature": temperature,
            "response_model": str(response_model) if response_model else None,
            "max_tokens": max_tokens,
            "input_tokens": input_tokens,
        }

        # Route to appropriate provider
        if self.provider == "gemini":
            return self._generate_gemini_completion(
                messages, temperature, response_model, context, max_tokens, request_data
            )
        elif self.provider == "deepseek":
            return self._generate_deepseek_completion(
                messages, temperature, response_model, context, max_tokens, request_data
            )
        else:
            return self._generate_openai_completion(
                messages, temperature, response_model, context, max_tokens, request_data
            )

    def _generate_openai_completion(
        self, messages, temperature, response_model, context, max_tokens, request_data
    ):
        """Generate completion using OpenAI API."""
        if response_model is None:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Save raw response
            response_data = {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": response.usage.model_dump() if response.usage else None,
                "response_id": response.id,
                "created": response.created,
            }
            self._save_raw_response(context, request_data, response_data, "chat")

            return response.choices[0].message.content
        else:
            response = self.client.chat.completions.parse(
                messages=messages,
                model=self.model,
                temperature=temperature,
                response_format=response_model,
                max_tokens=max_tokens,
            )

            # Save raw response for structured output
            response_data = {
                "parsed_content": (
                    response.choices[0].message.parsed.model_dump()
                    if response.choices[0].message.parsed
                    else None
                ),
                "raw_content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": response.usage.model_dump() if response.usage else None,
                "response_id": response.id,
                "created": response.created,
            }
            self._save_raw_response(
                context, request_data, response_data, "chat_structured"
            )

            return response.choices[0].message.parsed

    def _generate_deepseek_completion(
        self, messages, temperature, response_model, context, max_tokens, request_data
    ):
        """Generate completion using DeepSeek API.

        DeepSeek supports response_format={'type': 'json_object'} for JSON output,
        but doesn't support OpenAI's structured output with json_schema.
        We include the Pydantic schema in the prompt to guide the model.

        Key improvements over basic implementation:
        1. Retry logic with exponential backoff for structured output failures
        2. Schema placed at BEGINNING of user message for better attention
        3. Simplified schema representation for complex nested models
        4. Lenient validation with automatic field fixing
        5. Returns raw dict on validation failure instead of None (allows partial recovery)
        """
        if response_model is None:
            # Standard text completion
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Save raw response
            response_data = {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": response.usage.model_dump() if response.usage else None,
                "response_id": response.id,
                "created": response.created,
            }
            self._save_raw_response(context, request_data, response_data, "chat_deepseek")

            return response.choices[0].message.content
        else:
            # Structured output with retry logic
            max_retries = 3
            last_error = None
            last_parsed_json = None

            for attempt in range(max_retries):
                try:
                    result = self._attempt_deepseek_structured_completion(
                        messages=messages,
                        temperature=temperature,
                        response_model=response_model,
                        context=context,
                        max_tokens=max_tokens,
                        request_data=request_data,
                        attempt=attempt,
                    )

                    if result is not None:
                        return result

                except Exception as e:
                    last_error = e
                    print(f"⚠️ DeepSeek attempt {attempt + 1}/{max_retries} failed: {e}")

                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        wait_time = 2 ** attempt
                        print(f"   Retrying in {wait_time}s...")
                        time.sleep(wait_time)

            # All retries failed - try to return raw JSON dict for partial recovery
            print(f"❌ DeepSeek structured output failed after {max_retries} attempts")
            if last_parsed_json is not None:
                print(f"   Returning raw JSON dict for partial recovery")
                return last_parsed_json

            # If we have the raw JSON from the last attempt, return it
            if hasattr(self, '_last_deepseek_parsed_json') and self._last_deepseek_parsed_json:
                print(f"   Returning last parsed JSON for partial recovery")
                return self._last_deepseek_parsed_json

            raise ValueError(f"DeepSeek structured output failed after {max_retries} attempts: {last_error}")

    def _attempt_deepseek_structured_completion(
        self, messages, temperature, response_model, context, max_tokens, request_data, attempt: int
    ):
        """Single attempt at DeepSeek structured completion with improved schema handling."""

        modified_messages = [msg.copy() for msg in messages]

        # Get JSON schema from Pydantic model
        schema_instruction = self._create_deepseek_schema_instruction(response_model, attempt)

        # CRITICAL FIX: Place schema at BEGINNING of user message for better model attention
        # On retries, also add emphasis on common failure points
        if modified_messages and modified_messages[-1].get("role") == "user":
            original_content = modified_messages[-1]["content"]

            if attempt == 0:
                # First attempt: schema at beginning
                modified_messages[-1] = {
                    "role": "user",
                    "content": schema_instruction + "\n\n" + original_content + "\n\nRespond with valid JSON only. No markdown code blocks."
                }
            else:
                # Retry attempts: more explicit instructions
                retry_emphasis = self._get_retry_emphasis(response_model, attempt)
                modified_messages[-1] = {
                    "role": "user",
                    "content": schema_instruction + "\n\n" + retry_emphasis + "\n\n" + original_content + "\n\nRespond with valid JSON only. No markdown code blocks. No explanations."
                }

        response = self.client.chat.completions.create(
            messages=modified_messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"

        # Clean up response - remove markdown code blocks if present
        content = self._clean_json_response(content)

        # Try to parse and validate
        parsed_json = None
        parsed_result = None
        validation_error = None

        try:
            parsed_json = json.loads(content)
            self._last_deepseek_parsed_json = parsed_json  # Store for recovery

            if hasattr(response_model, "model_validate"):
                # Try strict validation first
                try:
                    parsed_result = response_model.model_validate(parsed_json)
                except Exception as strict_error:
                    # Try lenient validation with automatic fixing
                    parsed_result = self._lenient_validate(response_model, parsed_json, strict_error)
            else:
                parsed_result = parsed_json

        except json.JSONDecodeError as e:
            validation_error = f"JSON parse error: {e}"
            print(f"⚠️ DeepSeek JSON parse failed (attempt {attempt + 1}): {e}")
            # Try to extract JSON from response if it contains markdown
            extracted = self._extract_json_from_text(content)
            if extracted:
                try:
                    parsed_json = json.loads(extracted)
                    self._last_deepseek_parsed_json = parsed_json
                    if hasattr(response_model, "model_validate"):
                        parsed_result = self._lenient_validate(response_model, parsed_json, None)
                    else:
                        parsed_result = parsed_json
                except:
                    pass

        except Exception as e:
            validation_error = f"Validation error: {e}"
            print(f"⚠️ DeepSeek validation failed (attempt {attempt + 1}): {e}")

        # Save raw response
        response_data_to_save = {
            "parsed_content": parsed_json,
            "validated_content": parsed_result.model_dump() if hasattr(parsed_result, 'model_dump') else parsed_result,
            "raw_content": content,
            "finish_reason": response.choices[0].finish_reason,
            "usage": response.usage.model_dump() if response.usage else None,
            "response_id": response.id,
            "created": response.created,
            "attempt": attempt + 1,
            "validation_error": validation_error,
        }
        self._save_raw_response(context, request_data, response_data_to_save, f"chat_deepseek_structured_attempt{attempt + 1}")

        return parsed_result

    def _create_deepseek_schema_instruction(self, response_model, attempt: int) -> str:
        """Create optimized schema instruction for DeepSeek.

        Uses a simplified schema representation that's easier for the model to follow.
        """
        if not hasattr(response_model, "model_json_schema"):
            return ""

        schema = response_model.model_json_schema()

        # For first attempt, use full schema but formatted more clearly
        if attempt == 0:
            # Create a cleaner schema representation
            simplified = self._simplify_schema_for_prompt(schema)
            return f"""CRITICAL: You MUST respond with valid JSON matching this exact structure.

Required JSON Schema:
```json
{json.dumps(simplified, indent=2)}
```

RULES:
1. Include ALL required fields - missing fields will cause failure
2. Use exact field names as shown (case-sensitive)
3. Arrays must be arrays [], objects must be objects {{}}
4. No extra fields beyond what's specified
5. No null values for required fields"""

        else:
            # On retries, use even more explicit format with examples
            required_fields = self._extract_required_fields(schema)
            return f"""CRITICAL: Your previous response was invalid. You MUST respond with valid JSON.

Required top-level fields: {', '.join(required_fields)}

Full schema:
```json
{json.dumps(schema, indent=2)}
```

STRICT REQUIREMENTS:
1. Every required field MUST be present
2. Field names are CASE-SENSITIVE
3. Do not add any fields not in the schema
4. Arrays must be arrays [], not null
5. Return ONLY the JSON object, nothing else"""

    def _simplify_schema_for_prompt(self, schema: dict) -> dict:
        """Simplify a JSON schema for better LLM comprehension."""
        # Remove $defs and inline the definitions for cleaner output
        simplified = schema.copy()

        # Keep essential parts, remove verbose metadata
        keys_to_remove = ['$defs', 'definitions', 'title', 'description']
        for key in keys_to_remove:
            simplified.pop(key, None)

        return simplified

    def _extract_required_fields(self, schema: dict) -> List[str]:
        """Extract required field names from schema."""
        required = schema.get('required', [])
        properties = schema.get('properties', {})

        if not required and properties:
            # If no explicit required, assume all properties are required
            required = list(properties.keys())

        return required

    def _get_retry_emphasis(self, response_model, attempt: int) -> str:
        """Get additional emphasis text for retry attempts based on common failure patterns."""
        model_name = response_model.__name__ if hasattr(response_model, '__name__') else str(response_model)

        common_issues = {
            "OperationMap": "Ensure 'dependency_analysis', 'assertion_operations', and 'utility_operations' are all present.",
            "CCodeValidationResult": "Ensure 'explanation', 'validation_result', 'code_issues', and 'validation_summary' are all present.",
            "EnhancedTestDesigns": "Ensure 'metadata' and 'test_scenarios' are present. 'test_suite_summary' is optional.",
        }

        base_emphasis = f"RETRY ATTEMPT {attempt + 1}: Your previous JSON was invalid or incomplete."

        if model_name in common_issues:
            return f"{base_emphasis}\n{common_issues[model_name]}"

        return base_emphasis

    def _clean_json_response(self, content: str) -> str:
        """Clean up JSON response by removing markdown code blocks and extra whitespace."""
        content = content.strip()

        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Try to extract JSON object from text that may contain other content."""
        # Try to find JSON object pattern
        patterns = [
            r'\{[\s\S]*\}',  # Match outermost braces
            r'```json\s*([\s\S]*?)\s*```',  # Match code block
            r'```\s*([\s\S]*?)\s*```',  # Match generic code block
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1) if match.lastindex else match.group(0)
                # Verify it's valid JSON
                try:
                    json.loads(candidate)
                    return candidate
                except:
                    continue

        return None

    def _lenient_validate(self, response_model, parsed_json: dict, original_error) -> Any:
        """Attempt lenient validation with automatic field fixing.

        Common fixes:
        1. Convert null arrays to empty arrays []
        2. Add missing optional fields with defaults
        3. Handle extra fields by filtering them out
        4. Strip extra fields that aren't in the schema
        """
        if parsed_json is None:
            raise ValueError("Cannot validate None")

        fixed_json = self._fix_common_json_issues(parsed_json, response_model)

        try:
            # Try validation with fixed JSON
            return response_model.model_validate(fixed_json)
        except Exception as e:
            # If validation fails due to extra fields, try stripping them
            if "extra" in str(e).lower() or "forbidden" in str(e).lower():
                print(f"   Attempting to strip extra fields...")
                stripped_json = self._strip_extra_fields(fixed_json, response_model)
                try:
                    return response_model.model_validate(stripped_json)
                except Exception as strip_error:
                    print(f"⚠️ Validation after stripping also failed: {strip_error}")
                    raise strip_error
            else:
                print(f"⚠️ Lenient validation failed: {e}")
                raise e

    def _strip_extra_fields(self, data: dict, response_model) -> dict:
        """Strip fields from data that aren't in the Pydantic model schema.

        This handles the case where DeepSeek adds extra fields that cause
        validation to fail with 'extra fields not permitted' errors.
        """
        if not isinstance(data, dict):
            return data

        if not hasattr(response_model, "model_json_schema"):
            return data

        schema = response_model.model_json_schema()
        allowed_properties = set(schema.get('properties', {}).keys())

        if not allowed_properties:
            return data

        stripped = {}
        for key, value in data.items():
            if key in allowed_properties:
                # Recursively strip nested objects
                prop_schema = schema.get('properties', {}).get(key, {})

                if isinstance(value, dict) and '$ref' in prop_schema:
                    # This is a nested model - we'd need the $defs to fully strip
                    # For now, just pass through
                    stripped[key] = value
                elif isinstance(value, list):
                    # Handle arrays of objects
                    stripped[key] = value
                else:
                    stripped[key] = value
            else:
                print(f"   Stripped extra field: {key}")

        return stripped

    def _fix_common_json_issues(self, data: dict, response_model) -> dict:
        """Fix common JSON issues that cause validation failures."""
        if not isinstance(data, dict):
            return data

        fixed = data.copy()

        # Get schema to understand expected types
        if hasattr(response_model, "model_json_schema"):
            schema = response_model.model_json_schema()
            properties = schema.get('properties', {})

            for field_name, field_schema in properties.items():
                # Fix null arrays -> empty arrays
                if field_name in fixed and fixed[field_name] is None:
                    field_type = field_schema.get('type')
                    if field_type == 'array':
                        fixed[field_name] = []
                        print(f"   Fixed: {field_name} null -> []")
                    elif field_type == 'object':
                        fixed[field_name] = {}
                        print(f"   Fixed: {field_name} null -> {{}}")
                    elif field_type == 'string':
                        fixed[field_name] = ""
                        print(f"   Fixed: {field_name} null -> ''")

                # Recursively fix nested objects
                if field_name in fixed and isinstance(fixed[field_name], dict):
                    # Check if there's a $ref to another model
                    ref = field_schema.get('$ref', '')
                    if ref:
                        # For nested objects, recursively fix
                        fixed[field_name] = self._fix_nested_dict(fixed[field_name])

                # Fix nested arrays of objects
                if field_name in fixed and isinstance(fixed[field_name], list):
                    fixed[field_name] = [
                        self._fix_nested_dict(item) if isinstance(item, dict) else item
                        for item in fixed[field_name]
                    ]

        return fixed

    def _fix_nested_dict(self, data: dict) -> dict:
        """Recursively fix common issues in nested dictionaries."""
        if not isinstance(data, dict):
            return data

        fixed = {}
        for key, value in data.items():
            if value is None:
                # Try to infer type from key name
                if key.endswith('s') or key in ['items', 'list', 'array', 'elements']:
                    fixed[key] = []
                elif key in ['data', 'content', 'text', 'message']:
                    fixed[key] = ""
                else:
                    fixed[key] = value
            elif isinstance(value, dict):
                fixed[key] = self._fix_nested_dict(value)
            elif isinstance(value, list):
                fixed[key] = [
                    self._fix_nested_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                fixed[key] = value

        return fixed

    def _generate_gemini_completion(
        self, messages, temperature, response_model, context, max_tokens, request_data
    ):
        """Generate completion using Google Gemini API.

        Improvements matching DeepSeek fixes:
        1. Retry logic with exponential backoff for structured output failures
        2. Schema placed at BEGINNING of user message for better attention
        3. Lenient validation with automatic field fixing
        4. Returns raw dict on validation failure instead of None
        """
        import google.generativeai as genai

        # Convert OpenAI message format to Gemini format
        gemini_contents = self._convert_messages_to_gemini(messages)

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if response_model is None:
            # Standard text completion
            response = self.gemini_model.generate_content(
                gemini_contents,
                generation_config=generation_config,
            )

            content = response.text if response.text else ""

            # Save raw response
            response_data = {
                "content": content,
                "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else None,
                    "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else None,
                    "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else None,
                } if response.usage_metadata else None,
            }
            self._save_raw_response(context, request_data, response_data, "chat_gemini")

            return content
        else:
            # Structured output with retry logic
            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    result = self._attempt_gemini_structured_completion(
                        gemini_contents=gemini_contents,
                        temperature=temperature,
                        response_model=response_model,
                        context=context,
                        max_tokens=max_tokens,
                        request_data=request_data,
                        attempt=attempt,
                    )

                    if result is not None:
                        return result

                except Exception as e:
                    last_error = e
                    print(f"⚠️ Gemini attempt {attempt + 1}/{max_retries} failed: {e}")

                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"   Retrying in {wait_time}s...")
                        time.sleep(wait_time)

            # All retries failed - try to return raw JSON dict for partial recovery
            print(f"❌ Gemini structured output failed after {max_retries} attempts")
            if hasattr(self, '_last_gemini_parsed_json') and self._last_gemini_parsed_json:
                print(f"   Returning last parsed JSON for partial recovery")
                return self._last_gemini_parsed_json

            raise ValueError(f"Gemini structured output failed after {max_retries} attempts: {last_error}")

    def _attempt_gemini_structured_completion(
        self, gemini_contents, temperature, response_model, context, max_tokens, request_data, attempt: int
    ):
        """Single attempt at Gemini structured completion with improved schema handling."""
        import google.generativeai as genai

        modified_contents = [
            {**item} if isinstance(item, dict) else item
            for item in gemini_contents
        ]

        # Create schema instruction - place at BEGINNING for better attention
        schema_instruction = self._create_deepseek_schema_instruction(response_model, attempt)

        # Prepend schema to the last user message
        if modified_contents and len(modified_contents) > 0:
            last_content = modified_contents[-1]
            if isinstance(last_content, dict) and "parts" in last_content:
                if last_content["parts"]:
                    original_part = last_content["parts"][-1]
                    # Place schema at BEGINNING
                    last_content["parts"][-1] = schema_instruction + "\n\n" + original_part + "\n\nRespond with valid JSON only. No markdown."
            elif isinstance(last_content, str):
                modified_contents[-1] = schema_instruction + "\n\n" + last_content + "\n\nRespond with valid JSON only. No markdown."

        response = self.gemini_model.generate_content(
            modified_contents,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            ),
        )

        content = response.text if response.text else "{}"

        # Clean up response
        content = self._clean_json_response(content)

        # Try to parse and validate
        parsed_json = None
        parsed_result = None
        validation_error = None

        try:
            parsed_json = json.loads(content)
            self._last_gemini_parsed_json = parsed_json  # Store for recovery

            if hasattr(response_model, "model_validate"):
                try:
                    parsed_result = response_model.model_validate(parsed_json)
                except Exception as strict_error:
                    # Try lenient validation
                    parsed_result = self._lenient_validate(response_model, parsed_json, strict_error)
            else:
                parsed_result = parsed_json

        except json.JSONDecodeError as e:
            validation_error = f"JSON parse error: {e}"
            print(f"⚠️ Gemini JSON parse failed (attempt {attempt + 1}): {e}")
            # Try to extract JSON from response
            extracted = self._extract_json_from_text(content)
            if extracted:
                try:
                    parsed_json = json.loads(extracted)
                    self._last_gemini_parsed_json = parsed_json
                    if hasattr(response_model, "model_validate"):
                        parsed_result = self._lenient_validate(response_model, parsed_json, None)
                    else:
                        parsed_result = parsed_json
                except:
                    pass

        except Exception as e:
            validation_error = f"Validation error: {e}"
            print(f"⚠️ Gemini validation failed (attempt {attempt + 1}): {e}")

        # Save raw response
        response_data_to_save = {
            "parsed_content": parsed_json,
            "validated_content": parsed_result.model_dump() if hasattr(parsed_result, 'model_dump') else parsed_result,
            "raw_content": content,
            "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None,
            "usage": {
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else None,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else None,
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else None,
            } if response.usage_metadata else None,
            "attempt": attempt + 1,
            "validation_error": validation_error,
        }
        self._save_raw_response(context, request_data, response_data_to_save, f"chat_gemini_structured_attempt{attempt + 1}")

        return parsed_result

    def _convert_messages_to_gemini(self, messages):
        """
        Convert OpenAI message format to Gemini format.

        OpenAI format: [{"role": "system"|"user"|"assistant", "content": "..."}]
        Gemini format: [{"role": "user"|"model", "parts": ["..."]}]
        """
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Gemini handles system instructions differently
                # Prepend to the first user message or store for later
                system_instruction = content
            elif role == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [content]
                })
            else:  # user
                # If there's a system instruction, prepend it to the first user message
                if system_instruction:
                    content = f"{system_instruction}\n\n{content}"
                    system_instruction = None
                gemini_contents.append({
                    "role": "user",
                    "parts": [content]
                })

        # If there's still a system instruction (no user messages), add it as user
        if system_instruction:
            gemini_contents.insert(0, {
                "role": "user",
                "parts": [system_instruction]
            })

        return gemini_contents

    def create_embeddings_for_json(
        self,
        json_file_path: str,
        output_file_path: str = None,
        embedding_model: str = "text-embedding-3-small",
    ) -> Dict[str, Any]:
        """
        Create embeddings for functions in a JSON file.

        NOTE: Embeddings ALWAYS use OpenAI, regardless of the chat completion provider.
        DeepSeek, Gemini, and other providers don't have embedding APIs.

        Args:
            json_file_path: Path to the JSON file containing function data
            output_file_path: Path to save the JSON with embeddings (optional, defaults to input file with _embedded suffix)
            embedding_model: OpenAI embedding model to use

        Returns:
            Dictionary containing the original data with embeddings added
        """
        # CRITICAL: Always use OpenAI client for embeddings, regardless of provider
        # DeepSeek, Gemini, OpenRouter don't support embeddings API
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

        # Load the JSON file
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Determine output file path if not provided
        if output_file_path is None:
            base_name = os.path.splitext(json_file_path)[0]
            output_file_path = f"{base_name}_embedded.json"

        # Process functions and add embeddings
        if "functions" in data:
            print(f"Creating embeddings for {len(data['functions'])} functions...")

            for i, func in enumerate(data["functions"]):
                # Create input text for embedding
                embedding_text = self._create_embedding_text(func)

                try:
                    # Create embedding using OpenAI client (always)
                    embedding_response = openai_client.embeddings.create(
                        model=embedding_model, input=embedding_text
                    )
                    func["embedding"] = embedding_response.data[0].embedding

                    print(
                        f"Created embedding for function {i+1}/{len(data['functions'])}: {func.get('name', 'unknown')}"
                    )

                except Exception as e:
                    print(
                        f"Error creating embedding for function {func.get('name', 'unknown')}: {e}"
                    )
                    func["embedding"] = None

        # Process all_functions if it exists (combined report format)
        if "all_functions" in data:
            print(
                f"Creating embeddings for {len(data['all_functions'])} functions in combined report..."
            )

            for i, func in enumerate(data["all_functions"]):
                embedding_text = self._create_embedding_text(func)

                try:
                    # Create embedding using OpenAI client (always)
                    embedding_response = openai_client.embeddings.create(
                        model=embedding_model, input=embedding_text
                    )
                    func["embedding"] = embedding_response.data[0].embedding

                    print(
                        f"Created embedding for function {i+1}/{len(data['all_functions'])}: {func.get('name', 'unknown')}"
                    )

                except Exception as e:
                    print(
                        f"Error creating embedding for function {func.get('name', 'unknown')}: {e}"
                    )
                    func["embedding"] = None

        # Save the data with embeddings
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Embeddings saved to {output_file_path}")
        return data

    def _create_embedding_text(self, func: Dict[str, Any]) -> str:
        """
        Create text representation of a function for embedding.

        Args:
            func: Function dictionary containing metadata

        Returns:
            String representation for embedding
        """
        parts = []

        # Add function name (handle both 'name' and 'function_name' fields)
        func_name = func.get("name") or func.get("function_name")
        if func_name:
            parts.append(f"Function: {func_name}")

        # Add name
        if "name" in func:
            parts.append(f"Name: {func['name']}")

        # Add description if available
        if "description" in func and func["description"]:
            parts.append(f"Description: {func['description']}")

        # Add return type
        if "return_type" in func:
            parts.append(f"Returns: {func['return_type']}")

        # Handle parameters (can be list of dicts or strings)
        if "parameters" in func and func["parameters"]:
            param_strs = []
            for param in func["parameters"]:
                if isinstance(param, dict):
                    param_strs.append(
                        f"{param.get('type', '')} {param.get('name', '')}"
                    )
                else:
                    param_strs.append(str(param))
            parts.append(f"Parameters: {', '.join(param_strs)}")

        # Add location if available
        # if 'location' in func:
        #     parts.append(f"Location: {func['location']}")

        # Add code snippet if available
        # if 'code_snippet' in func and func['code_snippet']:
        #     parts.append(f"Code: {func['code_snippet']}")

        # Add function body if available
        # if 'function_body' in func and func['function_body']:
        #     parts.append(f"Body: {func['function_body']}")

        return "\n".join(parts)

    def batch_create_embeddings(
        self,
        json_files: List[str],
        output_dir: str = None,
        embedding_model: str = "text-embedding-3-small",
    ) -> List[str]:
        """
        Create embeddings for multiple JSON files.

        Args:
            json_files: List of JSON file paths
            output_dir: Directory to save embedded files (optional)
            embedding_model: OpenAI embedding model to use

        Returns:
            List of output file paths
        """
        output_files = []

        for json_file in json_files:
            try:
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    base_name = os.path.basename(json_file)
                    name_without_ext = os.path.splitext(base_name)[0]
                    output_file = os.path.join(
                        output_dir, f"{name_without_ext}_embedded.json"
                    )
                else:
                    output_file = None

                self.create_embeddings_for_json(json_file, output_file, embedding_model)
                output_files.append(output_file or json_file)

            except Exception as e:
                print(f"Error processing {json_file}: {e}")
                continue

        return output_files
