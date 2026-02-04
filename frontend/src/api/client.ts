import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 타입 정의
export interface CreateSessionResponse {
  run_id: string;
  state: Record<string, any>;
  messages?: ChatMessage[];
  current_step?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  run_id: string;
  messages: ChatMessage[];
  current_step: string;
  next_step?: string;
  state: Record<string, any>;
  ui_data?: Record<string, any>;
}

// API 함수들
export const api = {
  // 세션 생성
  createSession: async (rawText?: string): Promise<CreateSessionResponse> => {
    const response = await apiClient.post('/sessions/', { raw_text: rawText });
    return response.data;
  },

  // 챗봇 메시지 전송
  sendMessage: async (runId: string, message: string): Promise<ChatResponse> => {
    const response = await apiClient.post(`/chat/${runId}/message`, {
      message
    });
    return response.data;
  },

  // 채팅 히스토리 조회
  getChatHistory: async (runId: string): Promise<ChatResponse> => {
    const response = await apiClient.get(`/chat/${runId}/history`);
    return response.data;
  }
};

export default apiClient;