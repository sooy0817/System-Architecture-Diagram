import React, { useState } from 'react';

interface EdgesStepProps {
  scopeDetails: Record<string, any>;
  onSubmit: (edgeText: string) => void;
  loading: boolean;
}

const EdgesStep: React.FC<EdgesStepProps> = ({ scopeDetails, onSubmit, loading }) => {
  const [edgeText, setEdgeText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (edgeText.trim()) {
      onSubmit(edgeText.trim());
    }
  };

  // 스코프 목록 생성
  const scopes = Object.keys(scopeDetails || {});

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
        <div className="px-4 py-6 sm:p-8">
          <div className="grid max-w-4xl grid-cols-1 gap-x-6 gap-y-8">
            <div>
              <h2 className="text-base font-semibold leading-7 text-gray-900">연결 관계 정의</h2>
              <p className="mt-1 text-sm leading-6 text-gray-600">
                각 스코프 간의 연결 관계와 통신 흐름을 정의해주세요.
              </p>
            </div>

            {/* 완료된 스코프 목록 */}
            {scopes.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="text-md font-medium text-gray-900 mb-3">완료된 스코프 목록</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {scopes.map((scopeKey) => {
                    const scope = scopeDetails[scopeKey]?.scope;
                    return (
                      <div key={scopeKey} className="bg-white border border-gray-200 rounded px-3 py-2">
                        <div className="text-sm font-medium text-gray-900">
                          {scope?.display || scopeKey}
                        </div>
                        <div className="text-xs text-gray-500">
                          {scope?.center} - {scope?.zone}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="edge-text" className="block text-sm font-medium leading-6 text-gray-900">
                  연결 관계 정보
                </label>
                <div className="mt-2">
                  <textarea
                    id="edge-text"
                    name="edge-text"
                    rows={12}
                    value={edgeText}
                    onChange={(e) => setEdgeText(e.target.value)}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    placeholder={`스코프 간 연결 관계를 헤더로 구분하여 입력해주세요.

예시:
[의왕 내부망]
- 안성 내부망과 전용회선으로 연결
- DMZ망과 방화벽을 통해 연결
- 외부 시스템과 API Gateway 연결

[의왕 DMZ망]  
- 내부망에서 웹 서비스 제공
- 외부 인터넷과 연결
- 보안 정책: HTTPS만 허용

[안성 내부망]
- 의왕 내부망과 데이터 동기화
- 백업 센터 역할`}
                    required
                  />
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  [헤더] 형식으로 스코프를 구분하고, 각 스코프의 연결 관계를 상세히 기술해주세요.
                </p>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                >
                  {loading ? '처리 중...' : '구성도 생성 완료'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EdgesStep;