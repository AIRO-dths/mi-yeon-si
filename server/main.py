from fastapi import FastAPI, Request
import uvicorn
from fastapi.templating import Jinja2Templates

app = FastAPI()
template = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request):
    return template.TemplateResponse("index.html", {"request": request})

@app.get("/face")
def read_face(request: Request):
    return template.TemplateResponse("face.html", {"request": request})

@app.get("/chat")
def read_chat(request: Request):
    return template.TemplateResponse("chat.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    