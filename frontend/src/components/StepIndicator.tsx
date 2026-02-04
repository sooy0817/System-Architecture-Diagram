import React from 'react';
import { CheckIcon } from '@heroicons/react/24/solid';

interface Step {
  id: string;
  name: string;
  status: 'complete' | 'current' | 'upcoming';
}

interface StepIndicatorProps {
  currentStep: string;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({ currentStep }) => {
  const steps: Step[] = [
    { id: 'corp-center', name: '법인/센터', status: 'upcoming' },
    { id: 'networks', name: '네트워크', status: 'upcoming' },
    { id: 'scope-detail', name: '스코프 상세', status: 'upcoming' },
    { id: 'edges', name: '연결 관계', status: 'upcoming' },
    { id: 'done', name: '완료', status: 'upcoming' },
  ];

  // 현재 단계에 따라 상태 업데이트
  const updatedSteps = steps.map((step, index) => {
    const stepOrder = ['corp-center', 'networks', 'scope-detail', 'edges', 'done'];
    const currentIndex = stepOrder.indexOf(currentStep);
    
    if (index < currentIndex) {
      return { ...step, status: 'complete' as const };
    } else if (index === currentIndex) {
      return { ...step, status: 'current' as const };
    } else {
      return { ...step, status: 'upcoming' as const };
    }
  });

  return (
    <nav aria-label="Progress">
      <ol className="flex items-center">
        {updatedSteps.map((step, stepIdx) => (
          <li key={step.name} className={stepIdx !== updatedSteps.length - 1 ? 'pr-8 sm:pr-20' : ''}>
            <div className="flex items-center">
              <div className="flex items-center">
                {step.status === 'complete' ? (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600">
                    <CheckIcon className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                ) : step.status === 'current' ? (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-indigo-600 bg-white">
                    <span className="text-indigo-600 font-medium text-sm">{stepIdx + 1}</span>
                  </div>
                ) : (
                  <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-gray-300 bg-white">
                    <span className="text-gray-500 font-medium text-sm">{stepIdx + 1}</span>
                  </div>
                )}
                <span className={`ml-4 text-sm font-medium ${
                  step.status === 'complete' ? 'text-gray-900' : 
                  step.status === 'current' ? 'text-indigo-600' : 'text-gray-500'
                }`}>
                  {step.name}
                </span>
              </div>
              {stepIdx !== updatedSteps.length - 1 && (
                <div className="ml-8 sm:ml-20 h-0.5 w-full bg-gray-200" />
              )}
            </div>
          </li>
        ))}
      </ol>
    </nav>
  );
};

export default StepIndicator;