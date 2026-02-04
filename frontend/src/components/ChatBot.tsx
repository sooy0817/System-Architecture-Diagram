import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  CheckCircle, 
  RotateCcw, 
  Building2, 
  Server, 
  Network, 
  Zap,
  Clock,
  Loader2
} from 'lucide-react';
import { api, ChatMessage } from '../api/client';

interface ChatBotProps {
  runId: string | null;
  onSessionCreate: (runId: string) => void;
  initialMessages?: any[];
}

interface StepIndicatorProps {
  step: string;
  title: string;
  completed?: boolean;
  current?: boolean;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({ step, title, completed, current }) => {
  return (
    <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 ${
      current ? 'bg-blue-100 border border-blue-300 shadow-sm' : 
      completed ? 'bg-green-100 border border-green-300' : 
      'bg-gray-100 border border-gray-200'
    }`}>
      {completed ? (
        <CheckCircle className="w-4 h-4 text-green-600" />
      ) : current ? (
        <div className="w-4 h-4 rounded-full bg-blue-600 animate-pulse" />
      ) : (
        <div className="w-4 h-4 rounded-full bg-gray-300" />
      )}
      <span className={`text-sm font-medium ${
        current ? 'text-blue-800' : 
        completed ? 'text-green-800' : 
        'text-gray-600'
      }`}>
        {title}
      </span>
    </div>
  );
};

const ChatBot: React.FC<ChatBotProps> = ({ runId, onSessionCreate, initialMessages = [] }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState('corp-center');
  const [uiData, setUiData] = useState<Record<string, any> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 초기 메시지 설정
  useEffect(() => {
    if (!runId) return;
    
    // 백엔드에서 받은 초기 메시지가 있으면 사용
    if (initialMessages && initialMessages.length > 0) {
      setMessages(initialMessages);
    } else {
      // 없으면 기본 환영 메시지
      const welcomeMessage: ChatMessage = {
        role: 'assistant',
        content: '안녕하세요! 구성도 생성 도구입니다.\n\n어떤 법인의 구성도를 만들어드릴까요?\n법인명과 센터 정보를 알려주세요.\n\n예시: "법인은 은행이고 AWS, 의왕으로 구성되어있습니다"',
        timestamp: new Date().toISOString()
      };
      
      setMessages([welcomeMessage]);
    }
  }, [runId, initialMessages]);

  // 메시지 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !runId || loading) return;

    const messageToSend = inputMessage;
    setInputMessage(''); // 입력창 즉시 비우기
    setLoading(true);

    try {
      const response = await api.sendMessage(runId, messageToSend);
      
      setMessages(response.messages);
      setCurrentStep(response.current_step);
      setUiData(response.ui_data || null);
      
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const renderSidebar = () => {
    return (
      <div className="w-64 bg-white border-r border-gray-200 p-3 overflow-y-auto">
        <div className="space-y-3">
          {/* 진행 상황 헤더 */}
          <div className="flex items-center space-x-2 pb-2 border-b border-gray-200">
            <Network className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-semibold text-gray-900">진행 상황</h3>
          </div>

          {/* 1단계: 법인/센터 */}
          <div className={`border rounded-lg p-2 transition-all ${
            currentStep === 'corp-center' 
              ? 'border-blue-400 bg-blue-50' 
              : uiData?.corporation 
                ? 'border-green-300 bg-green-50' 
                : 'border-gray-200 bg-gray-50'
          }`}>
            <div className="flex items-center space-x-2 mb-2">
              <Building2 className={`w-3 h-3 ${
                currentStep === 'corp-center' ? 'text-blue-600' : 'text-green-600'
              }`} />
              <span className="text-xs font-semibold text-gray-900">
                1단계: 법인/센터
              </span>
              {uiData?.corporation && currentStep !== 'corp-center' && (
                <CheckCircle className="w-3 h-3 text-green-600 ml-auto" />
              )}
            </div>
            
            {uiData?.corporation ? (
              <div className="space-y-1 text-xs">
                <div className="flex items-start">
                  <span className="text-gray-600 w-12">법인:</span>
                  <span className="font-medium text-gray-900">{uiData.corporation}</span>
                </div>
                {uiData.centers && uiData.centers.length > 0 && (
                  <div className="flex items-start">
                    <span className="text-gray-600 w-12">센터:</span>
                    <span className="font-medium text-gray-900">
                      {uiData.centers.join(', ')}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-gray-500 italic">입력 대기 중...</div>
            )}
          </div>

          {/* 2단계: 네트워크 구성 (법인/센터 입력 후에만 표시) */}
          {uiData?.corporation && (
            <div className={`border rounded-lg p-2 transition-all ${
              currentStep === 'networks' 
                ? 'border-blue-400 bg-blue-50' 
                : uiData?.center_networks && Object.keys(uiData.center_networks).length > 0
                  ? 'border-green-300 bg-green-50' 
                  : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex items-center space-x-2 mb-2">
                <Network className={`w-3 h-3 ${
                  currentStep === 'networks' ? 'text-blue-600' : 'text-green-600'
                }`} />
                <span className="text-xs font-semibold text-gray-900">
                  2단계: 네트워크 구성
                </span>
                {uiData?.center_networks && Object.keys(uiData.center_networks).length > 0 && currentStep !== 'networks' && (
                  <CheckCircle className="w-3 h-3 text-green-600 ml-auto" />
                )}
              </div>
              
              {currentStep === 'networks' && uiData?.current_center && (
                <div className="mb-2 px-2 py-1 bg-yellow-100 border border-yellow-300 rounded text-xs">
                  <Zap className="w-3 h-3 inline text-orange-600 mr-1" />
                  현재: <span className="font-semibold">{uiData.current_center}</span>
                  {uiData.current_index !== undefined && uiData.total_centers && (
                    <span className="ml-1 text-gray-600">
                      ({uiData.current_index + 1}/{uiData.total_centers})
                    </span>
                  )}
                </div>
              )}
              
              {uiData?.center_networks && Object.keys(uiData.center_networks).length > 0 ? (
                <div className="space-y-1">
                  {Object.entries(uiData.center_networks).map(([center, info]: [string, any]) => (
                    <div key={center} className="text-xs bg-white rounded p-1.5 border border-gray-200">
                      <div className="font-medium text-gray-900">{center}</div>
                      <div className="text-gray-600">
                        {Array.isArray(info.zones) ? info.zones.join(', ') : info.zones}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-gray-500 italic">입력 대기 중...</div>
              )}
            </div>
          )}

          {/* 3단계: 스코프 상세 (모든 센터의 네트워크 입력 완료 후에만 표시) */}
          {uiData?.corporation && 
           uiData?.centers && 
           uiData?.center_networks && 
           Object.keys(uiData.center_networks).length === uiData.centers.length && 
           currentStep !== 'corp-center' && 
           currentStep !== 'networks' && (
            <div className={`border rounded-lg p-2 transition-all ${
              currentStep === 'scope-detail' 
                ? 'border-blue-400 bg-blue-50' 
                : currentStep === 'edges' || currentStep === 'done'
                  ? 'border-green-300 bg-green-50' 
                  : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex items-center space-x-2 mb-2">
                <Server className={`w-3 h-3 ${
                  currentStep === 'scope-detail' ? 'text-blue-600' : 'text-green-600'
                }`} />
                <span className="text-xs font-semibold text-gray-900">
                  3단계: 스코프 상세
                </span>
                {(currentStep === 'edges' || currentStep === 'done') && (
                  <CheckCircle className="w-3 h-3 text-green-600 ml-auto" />
                )}
              </div>
              
              {currentStep === 'scope-detail' ? (
                <div className="text-xs text-blue-700">입력 진행 중...</div>
              ) : (currentStep === 'edges' || currentStep === 'done') ? (
                <div className="text-xs text-green-700">✓ 완료</div>
              ) : (
                <div className="text-xs text-gray-500 italic">대기 중...</div>
              )}
            </div>
          )}

          {/* 4단계: 연결 관계 (스코프 상세 완료 후에만 표시) */}
          {(currentStep === 'edges' || currentStep === 'done') && (
            <div className={`border rounded-lg p-2 transition-all ${
              currentStep === 'edges' 
                ? 'border-blue-400 bg-blue-50' 
                : currentStep === 'done'
                  ? 'border-green-300 bg-green-50' 
                  : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex items-center space-x-2 mb-2">
                <Zap className={`w-3 h-3 ${
                  currentStep === 'edges' ? 'text-blue-600' : 'text-green-600'
                }`} />
                <span className="text-xs font-semibold text-gray-900">
                  4단계: 연결 관계
                </span>
                {currentStep === 'done' && (
                  <CheckCircle className="w-3 h-3 text-green-600 ml-auto" />
                )}
              </div>
              
              {currentStep === 'edges' ? (
                <div className="text-xs text-blue-700">입력 진행 중...</div>
              ) : currentStep === 'done' ? (
                <div className="text-xs text-green-700">✓ 완료</div>
              ) : (
                <div className="text-xs text-gray-500 italic">대기 중...</div>
              )}
            </div>
          )}

          {/* 전체 진행률 (하단에 고정) */}
          {uiData?.current_index !== undefined && uiData?.total_centers && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <div className="flex items-center space-x-2 mb-1">
                <Clock className="w-3 h-3 text-gray-600" />
                <span className="text-xs font-medium text-gray-800">전체 진행률</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 h-1.5 rounded-full transition-all duration-500" 
                  style={{ width: `${((uiData.current_index + 1) / uiData.total_centers) * 100}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 text-center mt-1">
                {Math.round(((uiData.current_index + 1) / uiData.total_centers) * 100)}%
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.role === 'user';
    
    // 백틱으로 감싸진 텍스트를 코드 블록으로 변환하고 줄바꿈 처리
    const formatContent = (content: string) => {
      const lines = content.split('\n');
      
      return lines.map((line, lineIdx) => (
        <div key={lineIdx} className={lineIdx > 0 ? 'mt-2' : ''}>
          {line.split(/(`[^`]+`)/).map((part, partIdx) => {
            if (part.startsWith('`') && part.endsWith('`')) {
              const codeText = part.slice(1, -1);
              return (
                <span 
                  key={partIdx} 
                  className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-mono mx-1 ${
                    isUser 
                      ? 'bg-blue-400 bg-opacity-30 text-blue-100' 
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {codeText}
                </span>
              );
            }
            return <span key={partIdx}>{part}</span>;
          })}
        </div>
      ));
    };
    
    return (
      <div key={index} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
        <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm ${
          isUser 
            ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' 
            : 'bg-white border border-gray-200 text-gray-900'
        }`}>
          <div className="text-sm leading-relaxed">
            {formatContent(message.content)}
          </div>
          {message.timestamp && (
            <div className={`flex items-center space-x-1 text-xs mt-3 pt-2 border-t ${
              isUser ? 'text-blue-100 border-blue-400' : 'text-gray-400 border-gray-200'
            }`}>
              <Clock className="w-3 h-3" />
              <span>
                {new Date(message.timestamp).toLocaleTimeString('ko-KR', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (!runId) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
          <div className="text-gray-500">세션을 초기화하는 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* 좌측 사이드바 */}
      {renderSidebar()}

      {/* 우측 채팅 영역 */}
      <div className="flex-1 flex flex-col">
        {/* 헤더 */}
        <div className="bg-white border-b border-gray-200 px-4 py-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg">
                <Network className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">구성도 생성 도구</h2>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>실시간 대화</span>
            </div>
          </div>
          
          {/* 단계 표시기 */}
          <div className="flex space-x-2 overflow-x-auto pb-2">
            <StepIndicator 
              step="corp-center" 
              title="법인/센터" 
              completed={currentStep !== 'corp-center'}
              current={currentStep === 'corp-center'}
            />
            <StepIndicator 
              step="networks" 
              title="네트워크" 
              completed={['scope-detail', 'edges', 'done'].includes(currentStep)}
              current={currentStep === 'networks'}
            />
            <StepIndicator 
              step="scope-detail" 
              title="상세정보" 
              completed={['edges', 'done'].includes(currentStep)}
              current={currentStep === 'scope-detail'}
            />
            <StepIndicator 
              step="edges" 
              title="연결관계" 
              completed={currentStep === 'done'}
              current={currentStep === 'edges'}
            />
            <StepIndicator 
              step="done" 
              title="완료" 
              completed={false}
              current={currentStep === 'done'}
            />
          </div>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-4 space-y-4">
          {messages.map((message, index) => renderMessage(message, index))}
          
          {loading && (
            <div className="flex justify-start mb-6">
              <div className="bg-white border border-gray-200 text-gray-900 max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-600">처리 중</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 입력 영역 */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)"
                className="w-full px-4 py-3 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none shadow-sm transition-all duration-200"
                rows={1}
                disabled={loading}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || loading}
              className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-2xl hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          {/* 도움말 */}
          <div className="mt-3 flex items-center justify-center space-x-2 text-xs text-gray-500">
            <RotateCcw className="w-3 h-3" />
            <span>언제든지 "다시"라고 입력하면 이전 단계로 돌아갈 수 있습니다</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;
