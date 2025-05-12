import React, { useState, useEffect } from 'react';
import { ExclamationCircleIcon, KeyIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

const ApiKeyInput = ({ onApiKeyChange }) => {
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [isValid, setIsValid] = useState(true);
  const [isSaved, setIsSaved] = useState(false);

  // Load key from localStorage on component mount
  useEffect(() => {
    const savedKey = localStorage.getItem('OPENAI_API_KEY');
    if (savedKey) {
      setApiKey(savedKey);
      setIsSaved(true);
      if (onApiKeyChange) onApiKeyChange(savedKey);
    }
  }, [onApiKeyChange]);

  const handleChange = (e) => {
    const value = e.target.value;
    setApiKey(value);
    setIsValid(value === '' || value.startsWith('sk-'));
    setIsSaved(false);
  };

  const handleSave = () => {
    if (!apiKey || !isValid) return;
    
    localStorage.setItem('OPENAI_API_KEY', apiKey);
    setIsSaved(true);
    if (onApiKeyChange) onApiKeyChange(apiKey);
  };

  const handleClear = () => {
    setApiKey('');
    setIsValid(true);
    setIsSaved(false);
    localStorage.removeItem('OPENAI_API_KEY');
    if (onApiKeyChange) onApiKeyChange('');
  };

  return (
    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200 mb-3">
      <div className="flex items-center mb-2">
        <KeyIcon className="h-5 w-5 text-gray-500 mr-2" />
        <span className="text-sm font-medium text-gray-700">
          OpenAI API Key (Optional)
        </span>
      </div>
      
      <div className="relative">
        <input
          type={showApiKey ? "text" : "password"}
          value={apiKey}
          onChange={handleChange}
          placeholder="sk-..."
          className={`block w-full pl-3 pr-10 py-2 text-sm border ${
            !isValid ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 
            isSaved ? 'border-green-300 focus:ring-green-500 focus:border-green-500' : 
            'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
          } rounded-md shadow-sm`}
        />
        <button
          type="button"
          onClick={() => setShowApiKey(!showApiKey)}
          className="absolute inset-y-0 right-0 px-3 flex items-center bg-transparent text-gray-500 hover:text-gray-700"
        >
          {showApiKey ? 
            <EyeSlashIcon className="h-4 w-4" aria-hidden="true" /> : 
            <EyeIcon className="h-4 w-4" aria-hidden="true" />
          }
        </button>
      </div>
      
      {!isValid && (
        <p className="mt-1 text-xs text-red-600 flex items-center">
          <ExclamationCircleIcon className="h-3 w-3 mr-1" />
          API keys should start with "sk-"
        </p>
      )}
      
      <div className="flex justify-between mt-2">
        <p className="text-xs text-gray-500">
          {isSaved ? (
            <span className="text-green-600">✓ API key saved</span>
          ) : (
            "Add your OpenAI API key to use your own credits"
          )}
        </p>
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={handleClear}
            disabled={!apiKey}
            className={`px-2 py-1 text-xs rounded ${
              !apiKey ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Clear
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!apiKey || !isValid}
            className={`px-2 py-1 text-xs rounded ${
              !apiKey || !isValid ? 'bg-blue-300 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApiKeyInput; 