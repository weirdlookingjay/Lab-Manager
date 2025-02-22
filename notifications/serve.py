from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from main import app

# Mount the static directory
app.mount("/static", StaticFiles(directory="notifications/static"), name="static")

if __name__ == "__main__":
    uvicorn.run("serve:app", host="0.0.0.0", port=8000, reload=True)
