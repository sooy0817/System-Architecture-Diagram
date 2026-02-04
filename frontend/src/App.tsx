import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import ChatBot from './components/ChatBot';

interface AppState {
  runId: string | null;
  loading: boolean;
  error: string | null;
  initialMessages: any[];
}

function App() {
  const [appState, setAppState] = useState<AppState>({
    runId: null,
    loading: false,
    error: null,
    initialMessages: []
  });

  // 세션 초기화
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setAppState(prev => ({ ...prev, loading: true, error: null }));
      const response = await api.createSession();
      setAppState(prev => ({
        ...prev,
        runId: response.run_id,
        loading: false,
        initialMessages: response.messages || []
      }));
    } catch (error) {
      setAppState(prev => ({
        ...prev,
        error: '세션 초기화에 실패했습니다.',
        loading: false
      }));
    }
  };

  const handleSessionCreate = (runId: string) => {
    setAppState(prev => ({ ...prev, runId }));
  };

  const handleRestart = () => {
    setAppState({ runId: null, loading: false, error: null, initialMessages: [] });
    initializeSession();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="h-screen flex flex-col">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div>
                <h1 className="text-2xl font-bold leading-tight tracking-tight text-gray-900">
                  구성도 생성 도구
                </h1>
                <p className="text-sm text-gray-600">
                  AI와 대화하며 네트워크 구성도를 생성합니다
                </p>
              </div>
              <button
                onClick={handleRestart}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                새로 시작하기
              </button>
            </div>
          </div>
        </header>
        
        <main className="flex-1 overflow-hidden">
          <div className="h-full mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            {/* 에러 메시지 */}
            {appState.error && (
              <div className="mt-4 rounded-md bg-red-50 p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">오류가 발생했습니다</h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{appState.error}</p>
                    </div>
                    <div className="mt-4">
                      <button
                        onClick={initializeSession}
                        className="bg-red-100 px-2 py-1 text-sm font-medium text-red-800 rounded-md hover:bg-red-200"
                      >
                        다시 시도
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 챗봇 영역 */}
            <div className="h-full py-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-full flex flex-col">
                <ChatBot 
                  runId={appState.runId}
                  onSessionCreate={handleSessionCreate}
                  initialMessages={appState.initialMessages}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;