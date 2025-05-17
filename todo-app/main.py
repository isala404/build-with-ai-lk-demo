from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import uuid
import structlog

# 1. Configure structlog for loggers obtained via structlog.get_logger()
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,  # Filter based on stdlib log levels
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(), # Render stack info for errors
        structlog.processors.format_exc_info,   # Render exception info
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),    # Render as JSON
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# 2. Define LOGGING_CONFIG for Uvicorn (and standard library logging)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Keep existing loggers (like uvicorn's)
    "formatters": {
        "json_formatter": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(), # Final rendering step
            "foreign_pre_chain": [ # Processors for stdlib log records
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.format_exc_info,
            ],
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
            "stream": "ext://sys.stdout", # Or sys.stderr
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False, # Avoid duplicate logging if child loggers are also configured
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },\n        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# 3. Get a structlog logger for this module
log = structlog.get_logger(__name__)

app = FastAPI()

# In-memory database
todos_db = {}

class TodoItem(BaseModel):
    id: Optional[str] = None
    title: str
    completed: bool = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

# Mount static files (for CSS, JS if needed later, though Tailwind will be via CDN in HTML)
# app.mount("/static", StaticFiles(directory="static"), name="static") # Not strictly needed if only index.html

# Templates
templates = Jinja2Templates(directory=".") # Assuming index.html is in the root

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/todos/", response_model=TodoItem, status_code=201)
async def create_todo(todo: TodoItem):
    todo.id = str(uuid.uuid4())
    todos_db[todo.id] = todo
    return todo

@app.get("/todos/", response_model=List[TodoItem])
async def get_todos():
    return list(todos_db.values())

@app.get("/todos/{todo_id}", response_model=TodoItem)
async def get_todo(todo_id: str):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos_db[todo_id]

@app.put("/todos/{todo_id}", response_model=TodoItem)
async def update_todo(todo_id: str, todo_update: TodoUpdate):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    stored_todo = todos_db[todo_id]
    update_data = todo_update.model_dump(exclude_unset=True)
    
    updated_todo = stored_todo.model_copy(update=update_data)
    todos_db[todo_id] = updated_todo
    return updated_todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    del todos_db[todo_id]

    remaining = list(todos_db.values())
    completed_count = sum(1 for t in remaining if t.completed)
    # Add check for zero division
    if len(remaining) == 0:
        completion_rate = 0
    else:
        completion_rate = completed_count / len(remaining)
    return {
        "todos": remaining,
        "completion_rate": completion_rate
    }

@app.get("/error")
async def raise_error(msg: str = Query(..., description="Error message to raise")):
    raise Exception(msg)

if __name__ == "__main__":
    import uvicorn
    # Pass the LOGGING_CONFIG to Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG) 