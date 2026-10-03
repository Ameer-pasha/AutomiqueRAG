async def generate(llm, question, context):
    return await llm.generate(question, context)
