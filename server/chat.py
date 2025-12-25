import os
from anthropic import Anthropic


class ChatBot:
    def __init__(self):
        CHAT_KEY = os.getenv("ANTHROPIC_API_KEY")
        
        # Claude API Client 초기화
        self.client = Anthropic(api_key=CHAT_KEY)
        
        # Claude Haiku 4.5 모델 사용 (가장 경제적)
        self.model_name = "claude-haiku-4-5-20251001"
        self.system_instruction = None
        self.conversation_history = []  # 대화 히스토리 추가

    def bot_set(self, name, user_gen="남자"):
        self.system_instruction = f"""너는 지우야. 여성이고 {name}의 친구. 상대는 {user_gen}인 {name}이야.
너는 외향적이고 활발한 성격. 지금은 약속 나와서 {name}와 대화 중이야.

중요한 규칙:
- 너는 항상 지우로서만 말해. {name}의 대사는 절대 만들지 마.
- 이모지, 괄호, 마크다운 사용 금지
- 2문장 이하로 자연스럽게 대화
- 재미있고 매력적이고 친근하고 공감 잘하는 대화
- 이미 '{name}, 안녕?' 하고 인사했어
- 총 6턴 대화 후 종료
- 마지막엔 {name}가 답할 수 있게 질문으로 끝내"""
        self.conversation_history = []  # 대화 히스토리 초기화

    def get_response(self, user_p: str):
        try:
            # 사용자 메시지를 히스토리에 추가
            self.conversation_history.append({
                "role": "user",
                "content": user_p
            })
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=80,  # 50→80으로 증가 (문장 끊김 방지)
                temperature=0.7,
                system=self.system_instruction,
                messages=self.conversation_history  # 전체 대화 히스토리 전달
            )
            
            # Claude API 응답에서 텍스트 추출
            bot_message = response.content[0].text
            
            # 봇 응답을 히스토리에 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": bot_message
            })
            
            return bot_message
            
        except Exception as e:
            print("❌ ChatBot error:", e)
            return "지금은 대답하기가 조금 어려워… 잠깐만 기다려줄래?"