from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import uuid
from jlogging import LOGGING_CONFIG

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

@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: str):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    del todos_db[todo_id]
    return

@app.get("/error")
async def raise_error(msg: str = Query(..., description="Error message to raise")):
    raise Exception(msg)

if __name__ == "__main__":
    import uvicorn
    # Pass the LOGGING_CONFIG to Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=LOGGING_CONFIG) 