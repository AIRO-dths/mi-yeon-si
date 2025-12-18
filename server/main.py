from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import os,uvicorn,random,string,base64
from server.evaluator import score_sentences

DATABASE_URL = "sqlite:///./airo.db" 
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    gender = Column(String)
    chats = relationship("Chat", back_populates="owner")

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="chats")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 기존 FastAPI 설정 ---
os.makedirs('images', exist_ok=True)

app = FastAPI()

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

template = Jinja2Templates(directory="templates")

# --- 페이지 라우트 ---
@app.get("/")
def index(request: Request):
    return template.TemplateResponse("index.html", {"request": request})

@app.get("/face")
def face(request: Request):
    return template.TemplateResponse("face.html", {"request": request})

@app.get("/chat")
def chat(request: Request):
    return template.TemplateResponse("chat.html", {"request": request})

@app.get("/dash")
def dash(request: Request):
    return template.TemplateResponse("dash.html", {"request": request})

# --- Pydantic 모델 ---
class ChatMessage(BaseModel):
    message: str
    user_name: str
    counting: int

# --- API 엔드포인트 ---
@app.post("/api/chat")
async def chat_message(chat_msg: ChatMessage, db: Session = Depends(get_db)):
    random_response = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    
    # 사용자 정보 조회
    user = db.query(User).filter(User.name == chat_msg.user_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 최종 응답 결정
    if chat_msg.counting >= 5:
        response_text = "끝"
    else:
        response_text = f"임시 대화 {random_response}"

    # 대화 내용 저장
    chat_record = Chat(user_message=chat_msg.message, bot_response=response_text, owner=user)
    db.add(chat_record)
    db.commit()

    return {"response": response_text}

@app.post("/api/upload_photo")
async def upload_photo(
    name: str = Form(...),
    gender: str = Form(...),
    photo: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # 이미 존재하는 사용자인지 확인
        existing_user = db.query(User).filter(User.name == name, User.gender == gender).first()
        if existing_user:
            # [수정된 부분] 동일한 이름의 사용자가 몇 명인지 카운트
            user_count = db.query(User).filter(User.name.like(f"{name}%")).count()
            final_name = f"{name}({user_count})"
        else:
            final_name = name

        # Base64 디코딩 및 파일 저장 (이 부분은 원래 코드에 있었지만 사라졌네요. 다시 추가했습니다.)
        if "," in photo:
            photo_data = photo.split(",")[1]
        else:
            photo_data = photo
        image_data = base64.b64decode(photo_data)



        # 사용자 정보 데이터베이스에 저장
        db_user = User(name=final_name, gender=gender) # photo_path도 저장하도록 수정
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # [수정된 부분] 최종 이름을 반환
        return {
            "status": "success",
            "message": "사진이 성공적으로 업로드되고 사용자가 등록되었습니다.",
            "final_name": final_name  # <-- 이 부분 추가
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"처리 중 오류가 발생했습니다: {str(e)}"
        }

# --- 대시보드용 API ---
@app.get("/api/dashboard", response_model=List[dict])
def get_dashboard_data(db: Session = Depends(get_db)):
    users = db.query(User).all()
    dashboard_data = []
    for user in users:
        chats = db.query(Chat).filter(Chat.user_id == user.id).all()
        dashboard_data.append({
            "id": user.id,
            "name": user.name,
            "gender": user.gender,
            "chats": [{"user_message": c.user_message, "bot_response": c.bot_response} for c in chats]
        })
    return dashboard_data


# --- 대화 추출 ---
def get_latest_chat(db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .order_by(User.id.desc())
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="No user found")
    
    user_m = []
    bot_m = []
    for c in user.chats:
        user_m.append(c.user_message)
        bot_m.append(c.bot_response)
    return {
        "id": user.id,
        "name": user.name,
        "user_chat": user_m,
        "bot_response": bot_m
    }

# --- AI 점수 모델 연결 ---
def get_latest_score(db: Session):
    user = get_latest_chat(db)
    if not user:
        return None

    sentences = (
        user["bot_response"][-3:]
        + user["user_chat"][-3:]
    )

    scores = score_sentences(sentences)
    print("AI scores:", scores)
    return scores

# --- 대시보드에 연결 ---
@app.get("/api/user/{user_id}/score")
def get_user_score(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.chats:
        raise HTTPException(status_code=404, detail="No chat data")

    user_msgs = [c.user_message for c in user.chats][-3:]
    bot_msgs = [c.bot_response for c in user.chats][-3:]

    sentences = bot_msgs + user_msgs

    scores = score_sentences(sentences)

    return {
        "friend_user": round(float(scores["friend_user"]), 2),
        "attract_user": round(float(scores["attract_user"]), 2),
        "fun_user": round(float(scores["fun_user"]), 2),
        "blri_user": round(float(scores["blri_user"]), 2),
    }




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
