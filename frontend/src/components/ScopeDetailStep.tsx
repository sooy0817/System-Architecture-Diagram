import React, { useState } from 'react';

interface ScopeDetailStepProps {
  currentScope: Record<string, any> | null;
  remaining: number;
  onSubmit: (detailText: string) => void;
  onNext: () => void;
  loading: boolean;
}

const ScopeDetailStep: React.FC<ScopeDetailStepProps> = ({ 
  currentScope, 
  remaining, 
  onSubmit, 
  onNext,
  loading 
}) => {
  const [detailText, setDetailText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (detailText.trim()) {
      onSubmit(detailText.trim());
      setDetailText(''); // 다음 스코프를 위해 초기화
    }
  };

  const handleNext = () => {
    onNext();
  };

  if (!currentScope) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
          <div className="px-4 py-6 sm:p-8 text-center">
            <h2 className="text-base font-semibold leading-7 text-gray-900">스코프 준비 중...</h2>
            <p className="mt-1 text-sm leading-6 text-gray-600">
              다음 스코프를 가져오고 있습니다.
            </p>
            <button
              onClick={handleNext}
              disabled={loading}
              className="mt-4 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
            >
              {loading ? '처리 중...' : '다음 스코프 가져오기'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
        <div className="px-4 py-6 sm:p-8">
          <div className="grid max-w-4xl grid-cols-1 gap-x-6 gap-y-8">
            <div>
              <h2 className="text-base font-semibold leading-7 text-gray-900">스코프 상세 정보</h2>
              <p className="mt-1 text-sm leading-6 text-gray-600">
                현재 스코프에 대한 상세 정보를 입력해주세요.
              </p>
            </div>

            {/* 현재 스코프 정보 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-blue-900">
                    {currentScope.display || `${currentScope.center} ${currentScope.zone}`}
                  </h3>
                  <p className="text-sm text-blue-700">
                    센터: {currentScope.center} | 영역: {currentScope.zone}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-blue-900">
                    남은 스코프: {remaining}개
                  </p>
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="detail-text" className="block text-sm font-medium leading-6 text-gray-900">
                  상세 정보
                </label>
                <div className="mt-2">
                  <textarea
                    id="detail-text"
                    name="detail-text"
                    rows={8}
                    value={detailText}
                    onChange={(e) => setDetailText(e.target.value)}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    placeholder={`${currentScope.display || currentScope.center + ' ' + currentScope.zone}에 대한 상세 정보를 입력해주세요.

예시:
- 서버 정보: WEB01, WAS01, DB01
- 네트워크 장비: L4 스위치, 방화벽
- 연결 정보: 외부 연계 시스템
- 기타 특이사항`}
                    required
                  />
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  이 정보는 후보 추출 단계에서 분석됩니다. 가능한 구체적으로 작성해주세요.
                </p>
              </div>

              <div className="flex justify-between">
                <div className="text-sm text-gray-500">
                  진행률: {Math.round(((remaining === 0 ? 1 : (1 - remaining / (remaining + 1))) * 100))}%
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                >
                  {loading ? '처리 중...' : remaining > 0 ? '다음 스코프' : '스코프 완료'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScopeDetailStep;