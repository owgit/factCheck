import React, { useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CloudArrowUpIcon, 
  DocumentTextIcon, 
  CheckCircleIcon, 
  PhotoIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  CheckIcon,
  XMarkIcon,
  QuestionMarkCircleIcon,
  ShareIcon,
  ArrowDownTrayIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  AcademicCapIcon,
  MicrophoneIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import DOMPurify from 'dompurify';

const MAX_UPLOAD_SIZE = parseInt(process.env.REACT_APP_MAX_UPLOAD_SIZE || '250', 10);
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const stageColors = ['from-blue-400 to-blue-500', 'from-purple-400 to-purple-500', 'from-pink-400 to-pink-500'];

// Helper function to extract fact check data from HTML content
const extractFactCheckData = (htmlContent) => {
  if (!htmlContent) return null;
  
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlContent, 'text/html');
  
  const resultEl = doc.querySelector('.result');
  const conclusionEl = doc.querySelector('.analysis p');
  const findingsEls = doc.querySelectorAll('.findings li');
  const sourcesEls = doc.querySelectorAll('.sources li');
  
  const findings = Array.from(findingsEls).map(el => {
    const claimText = el.querySelector('.claim-text')?.textContent || '';
    const accuracy = el.querySelector('.accuracy')?.textContent || '';
    const explanation = el.querySelector('.explanation')?.textContent || '';
    
    return { claimText, accuracy, explanation };
  });
  
  const sources = Array.from(sourcesEls).map(el => {
    const linkEl = el.querySelector('a');
    if (linkEl) {
      return {
        url: linkEl.getAttribute('href') || '#',
        description: linkEl.textContent || '',
        hasUrl: true
      };
    } else {
      return {
        url: '#',
        description: el.textContent || '',
        hasUrl: false
      };
    }
  });
  
  return {
    result: resultEl?.textContent || 'UNKNOWN',
    conclusion: conclusionEl?.textContent || '',
    findings,
    sources
  };
};

// Component for displaying fact checking results
const FactCheckResults = ({ htmlContent, onShare, onExport }) => {
  const factData = extractFactCheckData(htmlContent);
  
  if (!factData) {
    return (
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <p className="text-gray-500">No fact check data available</p>
      </div>
    );
  }

  const getResultColor = (result) => {
    result = result.toLowerCase();
    if (result === 'accurate' || result === 'true') return 'bg-green-100 text-green-800 border-green-200';
    if (result === 'mostly true') return 'bg-green-50 text-green-700 border-green-100';
    if (result === 'mixed') return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (result === 'consensus-based') return 'bg-blue-100 text-blue-800 border-blue-200';
    if (result === 'mostly false') return 'bg-red-50 text-red-700 border-red-100';
    if (result === 'false') return 'bg-red-100 text-red-800 border-red-200';
    if (result === 'unverified') return 'bg-gray-100 text-gray-800 border-gray-200';
    if (result === 'error') return 'bg-red-50 text-red-800 border-red-200';
    if (result === 'ai-generated') return 'bg-purple-100 text-purple-800 border-purple-200';
    return 'bg-blue-100 text-blue-800 border-blue-200';
  };
  
  // Binary truth evaluation - simplified for user comprehension
  const getBinaryTruthColor = (accuracy) => {
    accuracy = accuracy.toLowerCase();
    
    // Green for anything with some degree of truth
    if (accuracy.includes('accurate') || 
        accuracy.includes('mostly true') || 
        accuracy.includes('partly accurate') ||
        accuracy.includes('expert consensus') ||
        accuracy.includes('based on expert')) {
      return 'bg-green-100 text-green-700 border-green-200';
    }
    
    // Red for false claims and conspiracies
    if (accuracy.includes('false') || 
        accuracy.includes('conspiracy') || 
        accuracy.includes('misleading')) {
      return 'bg-red-100 text-red-700 border-red-200';
    }
    
    // Gray for unverified or unknown
    return 'bg-gray-100 text-gray-700 border-gray-200';
  };
  
  const getAccuracyIcon = (accuracy) => {
    accuracy = accuracy.toLowerCase();
    if (accuracy.includes('accurate') && !accuracy.includes('mostly') && !accuracy.includes('partly')) 
      return <CheckIcon className="w-5 h-5 text-green-500" />;
    if (accuracy.includes('mostly true')) 
      return <CheckIcon className="w-5 h-5 text-green-400" />;
    if (accuracy.includes('partly accurate')) 
      return <ExclamationCircleIcon className="w-5 h-5 text-yellow-500" />;
    if (accuracy.includes('mostly false')) 
      return <XMarkIcon className="w-5 h-5 text-red-400" />;
    if (accuracy.includes('false') && !accuracy.includes('mostly')) 
      return <XMarkIcon className="w-5 h-5 text-red-500" />;
    if (accuracy.includes('expert consensus') || accuracy.includes('based on expert')) 
      return <AcademicCapIcon className="w-5 h-5 text-blue-500" />;
    if (accuracy.includes('unable') || accuracy.includes('don\'t know')) 
      return <QuestionMarkCircleIcon className="w-5 h-5 text-gray-500" />;
    return <InformationCircleIcon className="w-5 h-5 text-blue-500" />;
  };

  // Binary truth icon - simplified for user comprehension
  const getBinaryTruthIcon = (accuracy) => {
    accuracy = accuracy.toLowerCase();
    
    // Checkmark for anything with some degree of truth
    if (accuracy.includes('accurate') || 
        accuracy.includes('mostly true') || 
        accuracy.includes('partly accurate') ||
        accuracy.includes('expert consensus') ||
        accuracy.includes('based on expert')) {
      return <CheckIcon className="w-5 h-5 text-green-500" />;
    }
    
    // X for false claims and conspiracies
    if (accuracy.includes('false') || 
        accuracy.includes('conspiracy') || 
        accuracy.includes('misleading')) {
      return <XMarkIcon className="w-5 h-5 text-red-500" />;
    }
    
    // Question mark for unverified or unknown
    return <QuestionMarkCircleIcon className="w-5 h-5 text-gray-500" />;
  };

  const getAccuracyClass = (accuracy) => {
    accuracy = accuracy.toLowerCase();
    if (accuracy.includes('accurate') && !accuracy.includes('mostly') && !accuracy.includes('partly'))
      return 'bg-green-100 text-green-800';
    if (accuracy.includes('mostly true'))
      return 'bg-green-50 text-green-700';
    if (accuracy.includes('partly accurate'))
      return 'bg-yellow-100 text-yellow-800';
    if (accuracy.includes('mostly false'))
      return 'bg-red-50 text-red-700';
    if (accuracy.includes('false') && !accuracy.includes('mostly'))
      return 'bg-red-100 text-red-800';
    if (accuracy.includes('expert consensus') || accuracy.includes('based on expert'))
      return 'bg-blue-100 text-blue-800';
    if (accuracy.includes('unable') || accuracy.includes('don\'t know'))
      return 'bg-gray-100 text-gray-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getResultIcon = (result) => {
    result = result.toLowerCase();
    if (result === 'accurate' || result === 'true')
      return <CheckCircleIcon className="h-10 w-10 text-green-500" />;
    if (result === 'mostly true')
      return <CheckCircleIcon className="h-10 w-10 text-green-400" />;
    if (result === 'mixed')
      return <ExclamationCircleIcon className="h-10 w-10 text-yellow-500" />;
    if (result === 'consensus-based')
      return <AcademicCapIcon className="h-10 w-10 text-blue-500" />;
    if (result === 'mostly false')
      return <XMarkIcon className="h-10 w-10 text-red-400" />;
    if (result === 'false')
      return <XMarkIcon className="h-10 w-10 text-red-500" />;
    if (result === 'unverified')
      return <QuestionMarkCircleIcon className="h-10 w-10 text-gray-500" />;
    if (result === 'error')
      return <ExclamationCircleIcon className="h-10 w-10 text-red-500" />;
    if (result === 'ai-generated')
      return <InformationCircleIcon className="h-10 w-10 text-purple-500" />;
    return <QuestionMarkCircleIcon className="h-10 w-10 text-gray-500" />;
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Result Summary Card */}
      <div className={`p-6 rounded-xl shadow-sm border ${getResultColor(factData.result)}`}>
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="flex flex-col md:flex-row items-center text-center md:text-left mb-4 md:mb-0">
            <div className="flex-shrink-0 mb-3 md:mb-0">
              {getResultIcon(factData.result)}
            </div>
            <div className="md:ml-4">
              <h2 className="text-3xl font-bold tracking-tight">{factData.result}</h2>
              <p className="mt-2 text-gray-700">{factData.conclusion}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={onShare}
              className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
              title="Share this fact check"
            >
              <ShareIcon className="h-5 w-5" />
            </button>
            <button 
              onClick={onExport}
              className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
              title="Export as PDF"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Claims Analysis */}
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h3 className="text-xl font-semibold mb-4">Claims Analysis</h3>
        <div className="space-y-4">
          {factData.findings.map((finding, index) => (
            <div key={index} className={`p-4 border rounded-lg hover:bg-gray-50 transition-colors ${getBinaryTruthColor(finding.accuracy)}`}>
              <div className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  {getBinaryTruthIcon(finding.accuracy)}
                </div>
                <div className="ml-3 w-full">
                  <div className="flex justify-between">
                    <p className="font-medium text-gray-900">{finding.claimText}</p>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAccuracyClass(finding.accuracy)}`}>
                      {finding.accuracy}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{finding.explanation}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Sources */}
      {factData.sources && factData.sources.length > 0 && (
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-xl font-semibold mb-4">Sources</h3>
          <ul className="space-y-2">
            {factData.sources.map((source, index) => (
              <li key={index} className="flex items-center">
                <InformationCircleIcon className="h-4 w-4 text-blue-500 mr-2" />
                {source.hasUrl ? (
                  <a 
                    href={source.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    {source.description}
                  </a>
                ) : (
                  <span className="text-gray-700">{source.description}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Add ModelInfo component
const ModelInfo = ({ models }) => {
  return (
    <div className="mt-4 text-xs text-gray-600 border-t pt-3 border-gray-200">
      <p className="font-medium text-gray-700 mb-1">AI Models Used:</p>
      <div className="flex flex-wrap gap-2">
        {models.transcription && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-100">
            <MicrophoneIcon className="h-3 w-3 mr-1" />
            Transcription: {models.transcription.name}
          </span>
        )}
        
        {models.fact_check && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-green-50 text-green-700 border border-green-100">
            <CheckCircleIcon className="h-3 w-3 mr-1" />
            Fact Check: {models.fact_check.name}
            {models.fact_check.type && models.fact_check.type.includes("Web Search") && (
              <span className="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-md bg-blue-100 text-blue-700 text-xs">
                <GlobeAltIcon className="h-2.5 w-2.5 mr-0.5" />
                Web
              </span>
            )}
          </span>
        )}
        
        {models.image_analysis && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-100">
            <PhotoIcon className="h-3 w-3 mr-1" />
            Image Analysis: {models.image_analysis.name}
          </span>
        )}
        
        {models.web_search && models.web_search !== "Not used" && models.web_search_enabled && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-100">
            <GlobeAltIcon className="h-3 w-3 mr-1" />
            Web Search: {models.web_search}
          </span>
        )}
      </div>
    </div>
  );
};

// Create a new WebSearchResults component
const WebSearchResults = ({ results }) => {
  const [expanded, setExpanded] = useState({});

  if (!results || results.length === 0) {
    return null;
  }

  const toggleExpanded = (index) => {
    setExpanded(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold mb-4 flex items-center text-gray-800">
        <GlobeAltIcon className="w-6 h-6 mr-2 text-blue-500" />
        Web Search Results
      </h3>
      
      {results.map((result, index) => (
        <div 
          key={index} 
          className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
        >
          <div 
            className="flex justify-between items-start cursor-pointer"
            onClick={() => toggleExpanded(index)}
          >
            <h4 className="font-medium text-gray-900 flex-1">{result.question}</h4>
            <button className="text-gray-500 hover:text-gray-700 mt-1">
              {expanded[index] ? 
                <ChevronUpIcon className="w-5 h-5" /> : 
                <ChevronDownIcon className="w-5 h-5" />
              }
            </button>
          </div>
          
          {expanded[index] && (
            <div className="mt-3 text-gray-700 bg-gray-50 p-3 rounded-lg">
              <div dangerouslySetInnerHTML={{ 
                __html: DOMPurify.sanitize(
                  result.answer 
                    ? result.answer
                        .replace(/\n\n/g, '<br/><br/>')
                        .replace(/\n/g, '<br/>')
                    : 'No result available'
                ) 
              }} />
              <div className="mt-2 text-xs text-gray-500">
                <p>Model: {result.model_used || 'Unknown'}</p>
                <p>Timestamp: {result.timestamp ? new Date(result.timestamp).toLocaleString() : 'Not available'}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

function App() {
  const [file, setFile] = useState(null);
  const [instagramLink, setInstagramLink] = useState('');
  const [freeText, setFreeText] = useState('');
  const [inputMode, setInputMode] = useState('file'); // 'file', 'instagram', or 'text'
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [stage, setStage] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const factCheckContentRef = useRef(null);
  const [transcriptionOpen, setTranscriptionOpen] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);

  const handleFile = useCallback((selectedFile) => {
    if (selectedFile && selectedFile.size > MAX_UPLOAD_SIZE * 1024 * 1024) {
      setError(`File size should not exceed ${MAX_UPLOAD_SIZE} MB`);
    } else {
      setFile(selectedFile);
      setError(null);
    }
  }, []);

  const handleDrag = useCallback((e, isDragging) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(isDragging);
  }, []);

  const handleDrop = useCallback((e) => {
    handleDrag(e, false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleDrag, handleFile]);

  const handleSubmit = useCallback(async (event) => {
    event.preventDefault();
    
    // Validate input based on mode
    if (inputMode === 'file' && !file) {
      setError('Please upload a file.');
      return;
    } else if (inputMode === 'instagram' && !instagramLink) {
      setError('Please provide an Instagram link.');
      return;
    } else if (inputMode === 'text' && !freeText.trim()) {
      setError('Please enter some text to fact-check.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setStage(1);

    try {
      let response;
      
      if (inputMode === 'text') {
        // Handle free text submission
        const formData = new FormData();
        formData.append('text', freeText);
        
        response = await axios.post(`${API_BASE_URL}/fact-check-text`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } else {
        // Handle file or Instagram URL submission
        const formData = new FormData();
        file ? formData.append('file', file) : formData.append('url', instagramLink);
        
        response = await axios.post(`${API_BASE_URL}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            if (percentCompleted === 100) setStage(2);
          }
        });
      }

      setStage(3);
      setResult(response.data);
      
      // Store model information if available in the response
      if (response.data.models) {
        setModelInfo(response.data.models);
      }
      
    } catch (error) {
      console.error('API Error:', error.response?.data);
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [file, instagramLink, freeText, inputMode]);

  const getFactCheckStatus = useCallback((factCheck) => {
    if (!factCheck) return { status: 'UNKNOWN', color: 'text-yellow-400' };
    const lowerCaseCheck = factCheck.toLowerCase();
    if (lowerCaseCheck.includes('accurate')) return { status: 'ACCURATE', color: 'text-green-500' };
    if (lowerCaseCheck.includes('mostly true')) return { status: 'MOSTLY TRUE', color: 'text-green-400' };
    if (lowerCaseCheck.includes('mixed')) return { status: 'MIXED', color: 'text-yellow-400' };
    if (lowerCaseCheck.includes('mostly false')) return { status: 'MOSTLY FALSE', color: 'text-red-400' };
    if (lowerCaseCheck.includes('false') && !lowerCaseCheck.includes('mostly')) return { status: 'FALSE', color: 'text-red-500' };
    if (lowerCaseCheck.includes('unverified')) return { status: 'UNVERIFIED', color: 'text-gray-400' };
    if (lowerCaseCheck.includes('ai-generated')) return { status: 'AI-GENERATED', color: 'text-purple-500' };
    return { status: 'UNKNOWN', color: 'text-yellow-400' };
  }, []);

  const stageLabels = ['Upload', 'Processing', 'Analyzing'];

  const handleShare = useCallback(() => {
    if (navigator.share) {
      navigator.share({
        title: 'Fact Check Results',
        text: `Fact check result: ${extractFactCheckData(result?.fact_check_html || result?.image_analysis)?.result || 'View my fact-check results'}`
      }).catch(err => {
        console.log('Sharing failed', err);
        setShareModalOpen(true);
      });
    } else {
      setShareModalOpen(true);
    }
  }, [result]);

  const copyToClipboard = useCallback(() => {
    const factData = extractFactCheckData(result?.fact_check_html || result?.image_analysis);
    if (!factData) return;
    
    const text = `Fact Check Result: ${factData.result}\n\nConclusion: ${factData.conclusion}\n\nClaims:\n${
      factData.findings.map(f => `- ${f.claimText}: ${f.accuracy}`).join('\n')
    }`;
    
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard');
      setShareModalOpen(false);
    });
  }, [result]);

  const exportAsPDF = useCallback(() => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      alert('Please allow popups for this website to export results');
      return;
    }

    const factData = extractFactCheckData(result?.fact_check_html || result?.image_analysis);
    if (!factData) return;
    
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Fact Check Results</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          .header { text-align: center; margin-bottom: 30px; }
          .result { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
          .conclusion { margin-bottom: 30px; }
          .sources, .findings { margin-bottom: 30px; }
          h2 { border-bottom: 1px solid #ddd; padding-bottom: 10px; }
          .claim { margin-bottom: 15px; padding-left: 20px; }
          .accuracy { font-weight: bold; }
          .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Fact Check Results</h1>
          <p>Generated on ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="result">Result: ${factData.result}</div>
        <div class="conclusion">${factData.conclusion}</div>
        
        <div class="findings">
          <h2>Claims Analysis</h2>
          ${factData.findings.map(f => `
            <div class="claim">
              <p><strong>${f.claimText}</strong></p>
              <p class="accuracy">Assessment: ${f.accuracy}</p>
              <p>${f.explanation}</p>
            </div>
          `).join('')}
        </div>
        
        ${factData.sources.length > 0 ? `
          <div class="sources">
            <h2>Sources</h2>
            <ul>
              ${factData.sources.map(s => `<li><a href="${s.url}">${s.description}</a></li>`).join('')}
            </ul>
          </div>
        ` : ''}
        
        <div class="footer">
          <p>This fact check is an automated analysis and should be verified with additional sources.</p>
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 500);
    
  }, [result]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 tracking-tight">
            AI-Powered Fact Check & Verification
          </h1>
          <p className="mt-3 text-xl text-gray-600">
            Verify claims in videos, Instagram posts, and text with advanced AI fact-checking
          </p>
        </header>

        <AnimatePresence mode="wait">
          <motion.section
            key="form"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="bg-white rounded-2xl shadow-xl overflow-hidden"
            aria-labelledby="upload-section"
          >
            <div className="p-6 sm:p-8">
              <div className="flex flex-col space-y-6">
                {/* Input Type Selector Tabs */}
                <div className="flex border-b border-gray-200" role="tablist" aria-label="Content type selection">
                  <button
                    onClick={() => setInputMode('file')}
                    className={`flex-1 py-3 text-center border-b-2 font-medium text-sm ${
                      inputMode === 'file'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    role="tab"
                    aria-selected={inputMode === 'file'}
                    aria-controls="file-upload-panel"
                    id="file-upload-tab"
                  >
                    <CloudArrowUpIcon className="w-5 h-5 inline-block mr-1" aria-hidden="true" />
                    <span>Upload Media</span>
                  </button>
                  <button
                    onClick={() => setInputMode('instagram')}
                    className={`flex-1 py-3 text-center border-b-2 font-medium text-sm ${
                      inputMode === 'instagram'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    role="tab"
                    aria-selected={inputMode === 'instagram'}
                    aria-controls="instagram-panel"
                    id="instagram-tab"
                  >
                    <span className="inline-block w-5 h-5 mr-1 relative top-[1px]" aria-hidden="true">
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 inline-block">
                        <path d="M12 2C14.717 2 15.056 2.01 16.122 2.06C17.187 2.11 17.912 2.277 18.55 2.525C19.21 2.779 19.766 3.123 20.322 3.678C20.8305 4.1779 21.224 4.78259 21.475 5.45C21.722 6.087 21.89 6.813 21.94 7.878C21.987 8.944 22 9.283 22 12C22 14.717 21.99 15.056 21.94 16.122C21.89 17.187 21.722 17.912 21.475 18.55C21.2247 19.2178 20.8311 19.8226 20.322 20.322C19.822 20.8303 19.2173 21.2238 18.55 21.475C17.913 21.722 17.187 21.89 16.122 21.94C15.056 21.987 14.717 22 12 22C9.283 22 8.944 21.99 7.878 21.94C6.813 21.89 6.088 21.722 5.45 21.475C4.78233 21.2245 4.17753 20.8309 3.678 20.322C3.16941 19.8222 2.77593 19.2175 2.525 18.55C2.277 17.913 2.11 17.187 2.06 16.122C2.013 15.056 2 14.717 2 12C2 9.283 2.01 8.944 2.06 7.878C2.11 6.812 2.277 6.088 2.525 5.45C2.77524 4.78218 3.1688 4.17732 3.678 3.678C4.17767 3.16923 4.78243 2.77573 5.45 2.525C6.088 2.277 6.812 2.11 7.878 2.06C8.944 2.013 9.283 2 12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M17.5 6.5L17.51 6.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </span>
                    <span>Instagram Link</span>
                  </button>
                  <button
                    onClick={() => setInputMode('text')}
                    className={`flex-1 py-3 text-center border-b-2 font-medium text-sm ${
                      inputMode === 'text'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                    role="tab"
                    aria-selected={inputMode === 'text'}
                    aria-controls="text-panel"
                    id="text-tab"
                  >
                    <DocumentTextIcon className="w-5 h-5 inline-block mr-1" aria-hidden="true" />
                    <span>Free Text</span>
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* File Upload Section */}
                  <div 
                    role="tabpanel" 
                    id="file-upload-panel" 
                    aria-labelledby="file-upload-tab"
                    hidden={inputMode !== 'file'}
                  >
                    {inputMode === 'file' && (
                      <div 
                        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
                        onDragOver={(e) => handleDrag(e, true)}
                        onDragEnter={(e) => handleDrag(e, true)}
                        onDragLeave={(e) => handleDrag(e, false)}
                        onDrop={handleDrop}
                      >
                        <input
                          type="file"
                          id="file-upload"
                          className="sr-only"
                          onChange={(e) => handleFile(e.target.files[0])}
                          accept=".mp4,.mov,.avi,.jpg,.jpeg,.png,.gif"
                          aria-describedby="file-upload-description"
                        />
                        <label
                          htmlFor="file-upload"
                          className="cursor-pointer flex flex-col items-center justify-center"
                        >
                          <CloudArrowUpIcon className="w-10 h-10 text-gray-400 mb-2" aria-hidden="true" />
                          <span className="text-sm font-medium text-gray-900">
                            {file ? file.name : 'Click to upload or drag and drop'}
                          </span>
                          <p className="text-xs text-gray-500 mt-1" id="file-upload-description">
                            MP4, MOV, AVI, JPG, JPEG, PNG up to {MAX_UPLOAD_SIZE}MB
                          </p>
                          {file && (
                            <button
                              type="button"
                              className="mt-2 text-xs text-red-600 hover:text-red-800"
                              onClick={(e) => {
                                e.preventDefault();
                                setFile(null);
                              }}
                              aria-label="Remove file"
                            >
                              Remove file
                            </button>
                          )}
                        </label>
                      </div>
                    )}
                  </div>

                  {/* Instagram Link Section */}
                  <div 
                    role="tabpanel" 
                    id="instagram-panel" 
                    aria-labelledby="instagram-tab"
                    hidden={inputMode !== 'instagram'}
                  >
                    {inputMode === 'instagram' && (
                      <div>
                        <label htmlFor="instagram-url" className="block text-sm font-medium text-gray-700 mb-2">
                          Instagram Post URL
                        </label>
                        <div className="mt-1 flex rounded-md shadow-sm">
                          <div className="relative flex items-stretch flex-grow">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                              <span className="text-gray-500 sm:text-sm" aria-hidden="true">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-5 h-5">
                                  <path d="M12 2C14.717 2 15.056 2.01 16.122 2.06C17.187 2.11 17.912 2.277 18.55 2.525C19.21 2.779 19.766 3.123 20.322 3.678C20.8305 4.1779 21.224 4.78259 21.475 5.45C21.722 6.087 21.89 6.813 21.94 7.878C21.987 8.944 22 9.283 22 12C22 14.717 21.99 15.056 21.94 16.122C21.89 17.187 21.722 17.912 21.475 18.55C21.2247 19.2178 20.8311 19.8226 20.322 20.322C19.822 20.8303 19.2173 21.2238 18.55 21.475C17.913 21.722 17.187 21.89 16.122 21.94C15.056 21.987 14.717 22 12 22C9.283 22 8.944 21.99 7.878 21.94C6.813 21.89 6.088 21.722 5.45 21.475C4.78233 21.2245 4.17753 20.8309 3.678 20.322C3.16941 19.8222 2.77593 19.2175 2.525 18.55C2.277 17.913 2.11 17.187 2.06 16.122C2.013 15.056 2 14.717 2 12C2 9.283 2.01 8.944 2.06 7.878C2.11 6.812 2.277 6.088 2.525 5.45C2.77524 4.78218 3.1688 4.17732 3.678 3.678C4.17767 3.16923 4.78243 2.77573 5.45 2.525C6.088 2.277 6.812 2.11 7.878 2.06C8.944 2.013 9.283 2 12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                  <path d="M17.5 6.5L17.51 6.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                  <path d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                              </span>
                            </div>
                            <input
                              type="text"
                              id="instagram-url"
                              value={instagramLink}
                              onChange={e => setInstagramLink(e.target.value)}
                              placeholder="https://www.instagram.com/p/..."
                              className="focus:ring-blue-500 focus:border-blue-500 block w-full rounded-md pl-10 sm:text-sm border-gray-300"
                              aria-describedby="instagram-url-description"
                            />
                          </div>
                        </div>
                        <p className="mt-2 text-sm text-gray-500" id="instagram-url-description">
                          Paste a direct link to an Instagram post or reel
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Free Text Section */}
                  <div 
                    role="tabpanel" 
                    id="text-panel" 
                    aria-labelledby="text-tab"
                    hidden={inputMode !== 'text'}
                  >
                    {inputMode === 'text' && (
                      <div>
                        <label htmlFor="free-text" className="block text-sm font-medium text-gray-700 mb-2">
                          Enter Text to Fact-Check
                        </label>
                        <textarea
                          id="free-text"
                          value={freeText}
                          onChange={e => setFreeText(e.target.value)}
                          rows={8}
                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          placeholder="Enter any text, claim, or statement you want to fact-check..."
                          aria-describedby="free-text-description"
                        ></textarea>
                        <p className="mt-2 text-sm text-gray-500" id="free-text-description">
                          Enter claims, news snippets, or any text you want to verify
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-center">
                    <button
                      type="submit"
                      disabled={loading}
                      className={`flex justify-center items-center py-2 px-6 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                        loading
                          ? 'bg-blue-300 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                      }`}
                      aria-live="polite"
                      aria-busy={loading}
                    >
                      {loading ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          {stageLabels[stage] || 'Processing'}
                        </>
                      ) : inputMode === 'file' ? (
                        'Upload & Analyze'
                      ) : inputMode === 'instagram' ? (
                        'Process Instagram Post'
                      ) : (
                        'Fact Check Text'
                      )}
                    </button>
                  </div>
                </form>

                {error && (
                  <div className="mt-4 text-center text-red-500" role="alert" aria-live="assertive">
                    {error}
                  </div>
                )}
              </div>
            </div>
          </motion.section>
        </AnimatePresence>

        {result && (
          <motion.article
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-6 bg-white rounded-2xl p-6 shadow-sm border border-gray-200"
          >
            <div 
              id="fact-check-results"
              className="space-y-6"
            >
              <div 
                className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg mb-6"
                role="status"
              >
                <div className="flex">
                  <div className="flex-shrink-0">
                    <CheckCircleIcon className="h-5 w-5 text-green-500" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-green-800">
                      Analysis Complete
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      Scroll down to see the detailed fact-checking results below.
                    </p>
                  </div>
                </div>
                
                {modelInfo && <ModelInfo models={modelInfo} />}
              </div>

              <div ref={factCheckContentRef}>
                {result.image_analysis ? (
                  <motion.section 
                    whileHover={{ scale: 1.01 }} 
                    className="bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                  >
                    <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-800">
                      <PhotoIcon className="w-6 h-6 mr-2 text-blue-500" aria-hidden="true" />
                      Image Fact Check
                    </h2>
                    <FactCheckResults 
                      htmlContent={result.image_analysis} 
                      onShare={handleShare}
                      onExport={exportAsPDF}
                    />
                  </motion.section>
                ) : (
                  <>
                    <motion.section 
                      whileHover={{ scale: 1.01 }} 
                      className="bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                    >
                      <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-800">
                        <CheckCircleIcon className="w-6 h-6 mr-2 text-blue-500" aria-hidden="true" />
                        Fact Check Results
                      </h2>
                      <FactCheckResults 
                        htmlContent={result.fact_check_html} 
                        onShare={handleShare}
                        onExport={exportAsPDF}
                      />
                      
                      {/* Add structured data for fact check results */}
                      {extractFactCheckData(result.fact_check_html) && (
                        <script type="application/ld+json" dangerouslySetInnerHTML={{
                          __html: JSON.stringify({
                            "@context": "https://schema.org",
                            "@type": "ClaimReview",
                            "url": window.location.href,
                            "itemReviewed": {
                              "@type": "Claim",
                              "appearance": {
                                "@type": "CreativeWork",
                                "name": "User submitted content"
                              }
                            },
                            "author": {
                              "@type": "Organization",
                              "name": "AI-Powered Fact Check"
                            },
                            "reviewRating": {
                              "@type": "Rating",
                              "ratingValue": extractFactCheckData(result.fact_check_html).result.toLowerCase().includes("accurate") ? "5" : "1",
                              "bestRating": "5",
                              "worstRating": "1",
                              "alternateName": extractFactCheckData(result.fact_check_html).result
                            },
                            "claimReviewed": extractFactCheckData(result.fact_check_html).findings.map(f => f.claimText).join("; ")
                          })
                        }} />
                      )}
                    </motion.section>
                    <motion.section 
                      whileHover={{ scale: 1.01 }} 
                      className="bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                    >
                      <h2 
                        onClick={() => setTranscriptionOpen(prev => !prev)}
                        className="text-xl font-semibold mb-4 flex items-center justify-between text-gray-800 cursor-pointer select-none"
                        aria-expanded={transcriptionOpen}
                        aria-controls="transcription-content"
                      >
                        <div className="flex items-center">
                          <DocumentTextIcon className="w-6 h-6 mr-2 text-blue-500" aria-hidden="true" />
                          Transcription
                        </div>
                        <button 
                          className="text-gray-500 hover:text-gray-700"
                          aria-label={transcriptionOpen ? "Collapse transcription" : "Expand transcription"}
                        >
                          {transcriptionOpen ? 
                            <ChevronUpIcon className="w-5 h-5" aria-hidden="true" /> : 
                            <ChevronDownIcon className="w-5 h-5" aria-hidden="true" />
                          }
                        </button>
                      </h2>
                      {transcriptionOpen && (
                        <div 
                          id="transcription-content"
                          className="bg-white p-4 rounded-xl overflow-auto text-gray-700 border border-gray-100"
                        >
                          {result.transcription.split('\n').map((paragraph, index) => (
                            <p key={index} className="mb-4">{paragraph}</p>
                          ))}
                        </div>
                      )}
                    </motion.section>
                  </>
                )}
              </div>

              {/* Add Web Search Results if available */}
              {result && result.web_search_results && result.web_search_results.length > 0 && (
                <motion.section 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="mt-6 bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                >
                  <WebSearchResults results={result.web_search_results} />
                </motion.section>
              )}
            </div>
          </motion.article>
        )}
        
        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>&copy; {new Date().getFullYear()} Fact Check - AI-Powered Verification Tool</p>
          <p className="mt-1">
            <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a> · 
            <a href="/terms" className="text-blue-600 hover:underline ml-2">Terms of Service</a> ·
            <a href="/about" className="text-blue-600 hover:underline ml-2">About</a>
          </p>
        </footer>
      </div>
    </main>
  );
}

export default App;