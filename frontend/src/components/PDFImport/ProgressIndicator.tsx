import React from 'react';

interface Step {
  number: number;
  title: string;
  description: string;
}

interface ProgressIndicatorProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  steps,
  currentStep,
  className = ''
}) => {
  return (
    <div className={`${className}`}>
      <nav aria-label="Progress">
        <ol className="flex items-center justify-center space-x-8">
          {steps.map((step, index) => {
            const isCompleted = step.number < currentStep;
            const isCurrent = step.number === currentStep;
            const isUpcoming = step.number > currentStep;

            return (
              <li key={step.number} className="flex items-center">
                <div className="flex flex-col items-center">
                  {/* Step Circle */}
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors duration-200 ${
                      isCompleted
                        ? 'bg-blue-600 border-blue-600 text-white'
                        : isCurrent
                        ? 'border-blue-600 bg-white text-blue-600'
                        : 'border-gray-300 bg-white text-gray-400'
                    }`}
                  >
                    {isCompleted ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <span className="text-sm font-medium">{step.number}</span>
                    )}
                  </div>

                  {/* Step Text */}
                  <div className="mt-3 text-center">
                    <p
                      className={`text-sm font-medium ${
                        isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
                      }`}
                    >
                      {step.title}
                    </p>
                    <p
                      className={`text-xs mt-1 ${
                        isCompleted || isCurrent ? 'text-gray-600' : 'text-gray-400'
                      }`}
                    >
                      {step.description}
                    </p>
                  </div>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="hidden sm:block ml-8 mr-8">
                    <div
                      className={`w-16 h-0.5 transition-colors duration-200 ${
                        step.number < currentStep ? 'bg-blue-600' : 'bg-gray-300'
                      }`}
                    />
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
};