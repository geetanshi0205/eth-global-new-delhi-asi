from uagents_adapter import MCPServerAdapter
from server import mcp
from uagents import Agent
from dotenv import load_dotenv
import os

load_dotenv()

mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,
    asi1_api_key=os.getenv("ASI1_API_KEY"),
    model="asi1-mini"
)

agent = Agent(name="Medical Report Publisher Agent", port=8002, seed="Medical Report Publisher Agent ETHGlobal New Delhi", mailbox=True, publish_agent_details=True)

for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    mcp_adapter.run(agent)