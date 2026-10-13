import tiktoken

# Load tiktoken cl100k_base encoder
bpe_encoder = tiktoken.get_encoding("cl100k_base")

CHAR_THRESHOLD = 60000


def create_message_payload(user_input: str) -> dict:
    """
    Layer 1: Takes user message and stores it into a message field inside a hash map.
    """
    message_map = {}
    
    if user_input is not None:
        message_map["message"] = str(user_input)
    else:
        message_map["message"] = ""
        
    return message_map


def validate_message_payload(message_map: dict) -> bool:
    """
    Layer 2: Checks if the message field exists and is not empty.
    """
    message = message_map.get("message", "")
    
    clean_message = message.strip()
    if len(clean_message) == 0:
        raise ValueError("Message field is empty. Please provide a valid prompt.")
        
    return True


def estimate_token_from_text(text: str) -> int:
    """
    Layer 3: Estimates token count based on character length.
    - If length > 60,000 characters: 4 characters = 1 token
    - If length <= 60,000 characters: BPE encoding with cl100k_base
    """
    char_count = len(text)
    
    if char_count > CHAR_THRESHOLD:
        # Heuristic estimation for large payloads
        estimated_tokens = char_count // 4
        if estimated_tokens == 0:
            estimated_tokens = 1
        return estimated_tokens
    else:
        # Exact BPE token calculation
        encoded_tokens = bpe_encoder.encode(text)
        return len(encoded_tokens)


def estimate_token(user_input: str) -> int:
    """
    Coordinates the full token estimation workflow:
    1. Stores user input in a hash map with a 'message' field.
    2. Validates that the message field is not empty.
    3. Calculates and returns total estimated tokens.
    """
    # Layer 1: Store message in hash map
    payload = create_message_payload(user_input)
    
    # Layer 2: Validate message field is not empty
    validate_message_payload(payload)
    
    # Layer 3: Calculate tokens
    message_text = payload["message"]
    total_tokens = estimate_token_from_text(message_text)
    
    return total_tokens
