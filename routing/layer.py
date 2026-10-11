from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder
from routing.utterances import EASY_UTTERANCES, MEDIUM_UTTERANCES

def extract_intent_text(user_prompt: str, char_limit: int = 400) -> str:
    """
    Extracts the first and last parts of a long prompt to bypass context limits.
    """
    string_length = len(user_prompt)
    max_allowed_length = char_limit * 2
    
    if string_length <= max_allowed_length:
        return user_prompt
        
    first_part = user_prompt[:char_limit]
    last_part = user_prompt[-char_limit:]
    
    condensed_prompt = first_part + " ... " + last_part
    return condensed_prompt


class TaskRouter:
    def __init__(self):
        # 1. Setup Easy Route with BGE-optimized threshold
        easy_route = Route(
            name="Easy", 
            utterances=EASY_UTTERANCES,
            score_threshold=0.60
        )
        
        # 2. Setup Medium Route with BGE-optimized threshold
        medium_route = Route(
            name="Medium", 
            utterances=MEDIUM_UTTERANCES,
            score_threshold=0.60
        )
        
        # 3. Setup the new local HuggingFace encoder (BAAI/bge-small-en-v1.5)
        self.encoder = HuggingFaceEncoder(name="BAAI/bge-small-en-v1.5")
        
        # 4. Initialize the SemanticRouter (with explicit .add() array)
        self.router = SemanticRouter(encoder=self.encoder, routes=[])
        self.router.add([easy_route, medium_route])

    def route_task(self, user_prompt: str) -> str:
        """
        Condenses the prompt and routes it to 'Easy' or 'Medium'.
        """
        condensed_prompt = extract_intent_text(
            user_prompt=user_prompt,
            char_limit=400
        )
        
        # Pass the condensed text to the semantic router instance
        route_choice = self.router(condensed_prompt)
        
        # If the router couldn't confidently classify it, default to Medium
        if route_choice.name is None:
            return "Medium"
            
        return route_choice.name
