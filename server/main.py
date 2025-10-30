from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
import uvicorn
import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import random
import string
import base64

os.makedirs('images', exist_ok=True)

app = FastAPI()

app.mount("/images", StaticFiles(directory="images"), name="images")

template = Jinja2Templates(directory="templates")

users = {"ㅇㅇ_남자": 0,"ㅇㅇ_여자": 0}

@app.get("/")
def index(request: Request):
    return template.TemplateResponse("index.html", {"request": request})

@app.get("/face")
def face(request: Request):
    return template.TemplateResponse("face.html", {"request": request})

@app.get("/chat")
def chat(request: Request):
    return template.TemplateResponse("chat.html", {"request": request})

class ChatMessage(BaseModel):
    message: str
    user_name: str
    counting: int

@app.post("/api/chat")
async def chat_message(chat_msg: ChatMessage):
    random_response = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    if chat_msg.counting == 5:
        return {"response": "결과"}
    return {"response": f"{chat_msg.user_name}님, {random_response}"}

@app.post("/api/upload_photo")
async def upload_photo(
    name: str = Form(...),
    gender: str = Form(...),
    photo: str = Form(...)
):
    try:
        if "," in photo:
            photo_data = photo.split(",")[1]
        else:
            photo_data = photo
            
        image_data = base64.b64decode(photo_data)

        filename = f"{name}_{gender}.png"
        filepath = os.path.join("images", filename)
        
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        return {
            "status": "success",
            "message": "사진이 성공적으로 업로드되었습니다.",
            "filename": filename,
            "filepath": f"/images/{filename}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"사진 업로드 중 오류가 발생했습니다: {str(e)}"
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
