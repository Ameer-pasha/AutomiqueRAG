class VisionProvider:
    async def page_to_markdown(self, image_bytes: bytes) -> str:
        raise NotImplementedError("Add a Qwen, Gemini, Claude, or GPT vision adapter.")
