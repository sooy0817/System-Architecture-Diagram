import React, { useState } from 'react';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface CorpCenterStepProps {
  onSubmit: (corporation: string, centers: string[]) => void;
  loading: boolean;
}

const CorpCenterStep: React.FC<CorpCenterStepProps> = ({ onSubmit, loading }) => {
  const [corporation, setCorporation] = useState('');
  const [centers, setCenters] = useState<string[]>(['']);

  const addCenter = () => {
    setCenters([...centers, '']);
  };

  const removeCenter = (index: number) => {
    setCenters(centers.filter((_, i) => i !== index));
  };

  const updateCenter = (index: number, value: string) => {
    const newCenters = [...centers];
    newCenters[index] = value;
    setCenters(newCenters);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validCenters = centers.filter(center => center.trim() !== '');
    if (corporation.trim() && validCenters.length > 0) {
      onSubmit(corporation.trim(), validCenters);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
        <div className="px-4 py-6 sm:p-8">
          <div className="grid max-w-2xl grid-cols-1 gap-x-6 gap-y-8">
            <div>
              <h2 className="text-base font-semibold leading-7 text-gray-900">법인 및 센터 정보</h2>
              <p className="mt-1 text-sm leading-6 text-gray-600">
                구성도를 생성할 법인명과 센터 목록을 입력해주세요.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="corporation" className="block text-sm font-medium leading-6 text-gray-900">
                  법인명
                </label>
                <div className="mt-2">
                  <input
                    type="text"
                    name="corporation"
                    id="corporation"
                    value={corporation}
                    onChange={(e) => setCorporation(e.target.value)}
                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    placeholder="예: 은행"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium leading-6 text-gray-900">
                  센터 목록
                </label>
                <div className="mt-2 space-y-2">
                  {centers.map((center, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={center}
                        onChange={(e) => updateCenter(index, e.target.value)}
                        className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        placeholder={`센터 ${index + 1} (예: 의왕)`}
                        required={index === 0}
                      />
                      {centers.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeCenter(index)}
                          className="inline-flex items-center p-1 text-red-600 hover:text-red-800"
                        >
                          <XMarkIcon className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addCenter}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                  >
                    <PlusIcon className="h-4 w-4 mr-1" />
                    센터 추가
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                >
                  {loading ? '처리 중...' : '다음 단계'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CorpCenterStep;