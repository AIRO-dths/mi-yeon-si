import pathlib
import textwrap
import google.generativeai as genai
from pydantic import BaseModel

class ChatBot:
    def __init__(self):
        CHAT_KEY = "AIzaSyA676Oqllep12vF0hYlsiaV7O7qlCXUYT8"
        genai.configure(api_key=CHAT_KEY)
        

    def bot_set(self,name,user_gen = "남자", bot_gen = "여자"):
        gender = user_gen
        bot_gender = bot_gen
        self.bot_setting = f"""
        우리는 친구야.
        내 이름은 {name}이야.
        오늘은 우리 둘이 약속을 잡고 나온거야.
        나는 {gender}야.
        너는 {bot_gender}야.
        너는 외향적이고 활발한 성격이야.
        이모지, 괄호, 마크다운은 쓰지 마.
        나와 대화한다고 생각하고 대사를 하면 돼.
        대사는 2문장 이하로 해.
        재미, 매력, 친근함, 공감 능력을 골고루 평가할 수 있게 자연스러운 대화를 해.
        너는 '{name}, 안녕?'이라 대사했어.
        인사는 끝났어.
        대화는 10번 진행되고 끝이야.
        마지막에는 최대한 유저가 대답할 수 있게 해.
        """

        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction= self.bot_setting
        )



    def get_response(self,user_p: str):
        try:
            response = self.model.generate_content(
                user_p,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    temperature=0.7
                )
            )

            generated_text = ""

            if hasattr(response, "text") and response.text:
                generated_text = response.text
            elif response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    generated_text = "".join(part.text for part in candidate.content.parts if hasattr(part, "text"))
            
            return generated_text
        except Exception as e:
            print("❌ ChatBot error:", e)
            return "지금은 대답하기가 조금 어려워… 잠깐만 기다려줄래?"