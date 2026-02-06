# Costs per 1,000,000 tokens
MODEL_COSTS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.15, "output": 0.60},  # Fallback for alias
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "text-embedding-3-small": {
        "input": 0.02,
        "output": 0.02,
    },  # Embedding usually input only
}


class CostService:
    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for a given model and token counts."""
        costs = MODEL_COSTS.get(model, MODEL_COSTS["gpt-4o-mini"])
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)

    @staticmethod
    def calculate_embedding_cost(model: str, tokens: int) -> float:
        """Calculate the cost for embeddings."""
        costs = MODEL_COSTS.get(model, MODEL_COSTS["text-embedding-3-small"])
        return round((tokens / 1_000_000) * costs["input"], 6)


cost_service = CostService()
