from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient, set_debug
import os
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

app = FastAPI()

set_debug(2)

async def run_agent_logic(query: str):
    """Runs the agent with the given query."""
    config = {
        "mcpServers": {
            "http": {
                "url": "https://34cd5342-9f6e-4334-a727-e3b88218acbd-prod.e1-us-east-azure.choreoapis.dev/default/github-mcp/v1.0/sse",
                "headers": {
                    "api-key": f"{os.getenv('MCP_AUTH_TOKEN')}"
                }
            }
        }
    }

    # Create MCPClient from config file
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17"))

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30, verbose=True)

    # Run the query
    result = await agent.run(
        query,
        max_steps=30,
    )
    return result

@app.post("/run_agent/")
async def run_agent_endpoint(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    print("New payload received", payload)
    service = (
        payload.get("event_info", {}).get("service")
        if "event_info" in payload else None
    )
    project_id = (
        payload.get("group_info", {}).get("project_id")
        if "group_info" in payload else None
    )
    log_message = (
        payload.get("event_info", {}).get("log_message")
        if "event_info" in payload else None
    )

    if service == "todo-app" and project_id == "neon-mote-460105-b0" and log_message:
        prompt = f"""
        A runtime error has occurred in the 'todo-app'.

        Error Log:
        ---
        {log_message}
        ---

        The application code is located in the 'todo-app' directory of the 'isala404/build-with-ai-lk-demo' GitHub repository.

        Please fix the above error by following the steps below:
        1. Review the error log.
        2. Determine the file that contains the error within the `todo-app` directory.
        3. Read the file and understand the code within the `todo-app` directory (get_file_contents).
        4. Create a new branch (create_branch)
        5. Implement the fix in the new branch (create_or_update_file)
        6. Open a Pull Request to the main branch (create_pull_request)

        DO NOT stop tool calling till the PR was created and do not add unnecessary comments or code changes.
        """

        # Schedule the agent logic to run in the background
        background_tasks.add_task(run_agent_logic, prompt)
        return {"status": "agent_triggered", "message": "Agent is running in the background."}
    else:
        return JSONResponse(
            status_code=400,
            content={
                "status": "ignored",
                "message": "Payload missing required fields or does not match target service and project ID."
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)