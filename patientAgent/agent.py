from uagents_adapter import MCPServerAdapter
from server import mcp
from uagents import Agent
from dotenv import load_dotenv
import os

load_dotenv()

# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,
    asi1_api_key=os.getenv("ASI_ONE_API_KEY"),
    model="asi1-mini"
)

agent = Agent(name="Patient Agent22", port=8002, seed="Patient Agent ETHGlobal New Delhi2", mailbox=True, publish_agent_details=True)

for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    mcp_adapter.run(agent)