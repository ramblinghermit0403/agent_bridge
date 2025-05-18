from fastapi import FastAPI, Request
from app.langchain_agent import get_agent
import nest_asyncio

nest_asyncio.apply()

app = FastAPI()


@app.get("/ask")
async def ask_agent(prompt: str):
    agent = await get_agent()
    print("Agent input keys:", agent.input_keys)
    print("Agent output keys:", agent.output_keys)
    response = agent.invoke({"input": prompt})

    return {"response": response}
