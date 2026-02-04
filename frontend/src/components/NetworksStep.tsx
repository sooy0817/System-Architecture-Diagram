import React, { useState } from 'react';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface NetworksStepProps {
  centers: string[];
  onSubmit: (data: {
    center_zones: Record<string, string>;
    center_devices?: Record<string, string>;
    external_networks?: Array<{ name: string; zones: string }>;
  }) => void;
  loading: boolean;
}

const NetworksStep: React.FC<NetworksStepProps> = ({ centers, onSubmit, loading }) => {
  const [centerZones, setCenterZones] = useState<Record<string, string>>(
    centers.reduce((acc, center) => ({ ...acc, [center]: '' }), {})
  );
  const [centerDevices, setCenterDevices] = useState<Record<string, string>>(
    centers.reduce((acc, center) => ({ ...acc, [center]: '' }), {})
  );
  const [externalNetworks, setExternalNetworks] = useState<Array<{ name: string; zones: string }>>([]);

  const addExternalNetwork = () => {
    setExternalNetworks([...externalNetworks, { name: '', zones: '' }]);
  };

  const removeExternalNetwork = (index: number) => {
    setExternalNetworks(externalNetworks.filter((_, i) => i !== index));
  };

  const updateExternalNetwork = (index: number, field: 'name' | 'zones', value: string) => {
    const updated = [...externalNetworks];
    updated[index][field] = value;
    setExternalNetworks(updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // 필수 필드 검증
    const hasValidZones = Object.values(centerZones).some(zone => zone.trim() !== '');
    if (!hasValidZones) {
      alert('최소 하나의 센터에 대해 네트워크 영역을 입력해주세요.');
      return;
    }

    const validExternalNetworks = externalNetworks.filter(
      network => network.name.trim() !== '' && network.zones.trim() !== ''
    );

    onSubmit({
      center_zones: centerZones,
      center_devices: centerDevices,
      external_networks: validExternalNetworks.length > 0 ? validExternalNetworks : undefined
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl">
        <div className="px-4 py-6 sm:p-8">
          <div className="grid max-w-4xl grid-cols-1 gap-x-6 gap-y-8">
            <div>
              <h2 className="text-base font-semibold leading-7 text-gray-900">네트워크 및 장비 정보</h2>
              <p className="mt-1 text-sm leading-6 text-gray-600">
                각 센터의 네트워크 영역과 장비 정보를 입력해주세요.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              {/* 센터별 네트워크 정보 */}
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">센터별 네트워크 정보</h3>
                {centers.map((center) => (
                  <div key={center} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="text-md font-medium text-gray-800 mb-4">{center} 센터</h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium leading-6 text-gray-900">
                          네트워크 영역 *
                        </label>
                        <div className="mt-2">
                          <textarea
                            value={centerZones[center]}
                            onChange={(e) => setCenterZones({ ...centerZones, [center]: e.target.value })}
                            rows={3}
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                            placeholder="예: 내부망, DMZ망, 대외망"
                          />
                        </div>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium leading-6 text-gray-900">
                          장비 정보 (선택)
                        </label>
                        <div className="mt-2">
                          <textarea
                            value={centerDevices[center]}
                            onChange={(e) => setCenterDevices({ ...centerDevices, [center]: e.target.value })}
                            rows={3}
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                            placeholder="예: 외부GSLB, SK회선, 방화벽"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 외부 네트워크 */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">외부 네트워크 (선택)</h3>
                  <button
                    type="button"
                    onClick={addExternalNetwork}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                  >
                    <PlusIcon className="h-4 w-4 mr-1" />
                    외부 네트워크 추가
                  </button>
                </div>

                {externalNetworks.map((network, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-md font-medium text-gray-800">외부 네트워크 {index + 1}</h4>
                      <button
                        type="button"
                        onClick={() => removeExternalNetwork(index)}
                        className="inline-flex items-center p-1 text-red-600 hover:text-red-800"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium leading-6 text-gray-900">
                          네트워크 이름
                        </label>
                        <div className="mt-2">
                          <input
                            type="text"
                            value={network.name}
                            onChange={(e) => updateExternalNetwork(index, 'name', e.target.value)}
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                            placeholder="예: 중계기관"
                          />
                        </div>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium leading-6 text-gray-900">
                          네트워크 영역
                        </label>
                        <div className="mt-2">
                          <input
                            type="text"
                            value={network.zones}
                            onChange={(e) => updateExternalNetwork(index, 'zones', e.target.value)}
                            className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                            placeholder="예: 대외망"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
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

export default NetworksStep;