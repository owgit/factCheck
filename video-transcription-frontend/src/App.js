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
      </div>
    </div>
  );
};

function App() {
  const [file, setFile] = useState(null);
  const [instagramLink, setInstagramLink] = useState('');
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
    if (!file && !instagramLink) {
      setError('Please upload a file or provide an Instagram link.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setStage(1);

    const formData = new FormData();
    file ? formData.append('file', file) : formData.append('url', instagramLink);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          if (percentCompleted === 100) setStage(2);
        }
      });

      setStage(3);
      setResult(response.data);
      
      // Store model information if available in the response
      if (response.data.models) {
        setModelInfo(response.data.models);
      }
      
      // No auto-scrolling - let user navigate naturally
    } catch (error) {
      console.error('API Error:', error.response?.data);
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [file, instagramLink]);

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4 md:p-8 relative overflow-hidden">
      {stage > 0 && loading && (
        <div className="fixed top-0 left-0 w-full z-50">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-400 to-purple-600"
              initial={{ width: 0 }}
              animate={{ width: `${(stage / 3) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <div className="flex justify-between px-4 pt-1 text-xs text-gray-600">
            {stageLabels.map((label, index) => (
              <div key={index} className={`flex flex-col items-center ${stage > index ? 'text-blue-600 font-medium' : ''}`}>
                <span>{label}</span>
                {stage > index && <CheckIcon className="h-4 w-4 text-green-500" />}
              </div>
            ))}
          </div>
        </div>
      )}

      {shareModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Share Results</h3>
            <div className="space-y-4">
              <button 
                onClick={copyToClipboard}
                className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center"
              >
                <span>Copy to clipboard</span>
              </button>
              <button 
                onClick={exportAsPDF}
                className="w-full py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center justify-center"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                <span>Export as PDF</span>
              </button>
            </div>
            <button 
              onClick={() => setShareModalOpen(false)}
              className="mt-4 w-full py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <AnimatePresence>
        <motion.div
          key={loading ? 'loading' : 'content'}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto bg-white bg-opacity-90 rounded-3xl shadow-lg overflow-hidden relative"
        >
          <div className="p-4 md:p-8">
            <h1 className="text-3xl md:text-4xl font-bold mb-6 md:mb-8 text-gray-800">Fact Checker</h1>
            
            <motion.form onSubmit={handleSubmit} className="mb-8" whileHover={{ scale: 1.02 }} transition={{ type: "spring", stiffness: 300 }}>
              <label
                htmlFor="dropzone-file"
                className={`flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-2xl cursor-pointer bg-gray-50 hover:bg-gray-100 transition-all duration-300 ${isDragging ? 'border-blue-500 bg-blue-50' : ''}`}
                onDragEnter={(e) => handleDrag(e, true)}
                onDragOver={(e) => handleDrag(e, true)}
                onDragLeave={(e) => handleDrag(e, false)}
                onDrop={handleDrop}
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <CloudArrowUpIcon className={`w-12 h-12 mb-4 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`} />
                  <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                  <p className="text-xs text-gray-500">MP4, PNG, JPG, JPEG, GIF (MAX. {MAX_UPLOAD_SIZE}MB)</p>
                </div>
                <input id="dropzone-file" type="file" className="hidden" onChange={(e) => handleFile(e.target.files[0])} accept=".mp4,.png,.jpg,.jpeg,.gif" />
              </label>
              {file && <p className="mt-2 text-sm text-gray-600 font-medium">{file.name}</p>}
              <p className="mt-4 text-center text-gray-600">OR</p>
              <input
                type="text"
                className="mt-4 w-full py-3 px-4 border border-gray-300 rounded-xl shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300"
                placeholder="Enter Instagram Video Link"
                value={instagramLink}
                onChange={(e) => setInstagramLink(e.target.value)}
                disabled={loading}
              />
              <motion.button
                type="submit"
                className={`mt-4 w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-md hover:from-blue-600 hover:to-purple-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300 ${loading ? 'py-5' : ''}`}
                whileHover={{ scale: loading ? 1 : 1.05 }}
                whileTap={{ scale: loading ? 1 : 0.95 }}
                disabled={(file === null && instagramLink === '') || loading}
              >
                {loading ? (
                  <div className="flex flex-col items-center space-y-2">
                    <div className="flex items-center justify-center">
                      <svg className="animate-spin h-5 w-5 text-white mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="font-medium">
                        {stage === 1 ? "Uploading your content..." : 
                         stage === 2 ? "Processing your media..." : 
                                       "Analyzing for facts..."}
                      </span>
                    </div>
                    <span className="text-xs text-white text-opacity-90">
                      {stage === 1 ? "Uploading your file" : 
                       stage === 2 ? "Processing content for analysis" : 
                                     "Fact-checking against reliable sources"}
                    </span>
                  </div>
                ) : 'Upload and Process'}
              </motion.button>
            </motion.form>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-lg"
                role="alert"
              >
                <p>{error}</p>
              </motion.div>
            )}

            {loading && (
              <div className="flex justify-center mb-8 mt-2">
                <div className="space-y-2 w-3/4">
                  <div className="bg-gray-200 h-2 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-blue-400 to-purple-600"
                      initial={{ width: 0 }}
                      animate={{ width: `${(stage / 3) * 100}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
              </div>
            )}

            {result && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="space-y-6"
              >
                <div 
                  id="fact-check-results"
                  className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg mb-6"
                >
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
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
                  
                  {/* Add ModelInfo component here */}
                  {modelInfo && <ModelInfo models={modelInfo} />}
                </div>

                <div ref={factCheckContentRef}>
                  {result.image_analysis ? (
                    <motion.div 
                      whileHover={{ scale: 1.01 }} 
                      className="bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                    >
                      <h3 className="text-xl font-semibold mb-4 flex items-center text-gray-800">
                        <PhotoIcon className="w-6 h-6 mr-2 text-blue-500" />
                        Image Fact Check
                      </h3>
                      <FactCheckResults 
                        htmlContent={result.image_analysis} 
                        onShare={handleShare}
                        onExport={exportAsPDF}
                      />
                    </motion.div>
                  ) : (
                    <>
                      <motion.div 
                        whileHover={{ scale: 1.01 }} 
                        className="bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                      >
                        <h3 className="text-xl font-semibold mb-4 flex items-center text-gray-800">
                          <CheckCircleIcon className="w-6 h-6 mr-2 text-blue-500" />
                          Fact Check Results
                        </h3>
                        <FactCheckResults 
                          htmlContent={result.fact_check_html} 
                          onShare={handleShare}
                          onExport={exportAsPDF}
                        />
                      </motion.div>
                      <motion.div 
                        whileHover={{ scale: 1.01 }} 
                        className="bg-gray-50 rounded-2xl p-6 shadow-sm border border-gray-100"
                      >
                        <h3 
                          onClick={() => setTranscriptionOpen(prev => !prev)}
                          className="text-xl font-semibold mb-4 flex items-center justify-between text-gray-800 cursor-pointer select-none"
                        >
                          <div className="flex items-center">
                            <DocumentTextIcon className="w-6 h-6 mr-2 text-blue-500" />
                            Transcription
                          </div>
                          <button className="text-gray-500 hover:text-gray-700">
                            {transcriptionOpen ? 
                              <ChevronUpIcon className="w-5 h-5" /> : 
                              <ChevronDownIcon className="w-5 h-5" />
                            }
                          </button>
                        </h3>
                        {transcriptionOpen && (
                          <div className="bg-white p-4 rounded-xl overflow-auto text-gray-700 border border-gray-100">
                            {result.transcription.split('\n').map((paragraph, index) => (
                              <p key={index} className="mb-4">{paragraph}</p>
                            ))}
                          </div>
                        )}
                      </motion.div>
                    </>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
      
      <div className="text-center mt-8 text-sm text-gray-500">
        <p>This tool attempts to verify content but may not catch all misinformation.</p>
        <p>Always cross-check important information with multiple reliable sources.</p>
        {modelInfo && (
          <div className="mt-2 text-xs">
            <p>
              Powered by OpenAI models
            </p>
            {modelInfo.fact_check && modelInfo.fact_check.type && modelInfo.fact_check.type.includes("Web Search") && (
              <p className="mt-1 text-blue-600">
                <span className="inline-flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                  </svg>
                  Using real-time web search for fact verification
                </span>
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;