import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const About = () => {
  React.useEffect(() => {
    document.title = "About - Fact Check";
  }, []);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <Link 
          to="/"
          className="inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-900 group bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded-md transition-colors"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2 text-blue-600 group-hover:text-blue-800" aria-hidden="true" />
          Back to Home
        </Link>
      </div>

      <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-2xl font-semibold text-gray-800">About Fact Check</h1>
        </div>
        <div className="p-6 prose prose-lg max-w-none text-gray-700">
          <p>
            Welcome to the AI-Powered Fact Check & Verification tool!
          </p>
          
          <p>
            Our mission is to help you quickly and easily verify the accuracy of 
            information found in videos, Instagram posts, images, and text. In an era 
            of rapid information spread, distinguishing fact from fiction is more 
            important than ever.
          </p>

          <h2>How It Works</h2>
          <p>
            We utilize cutting-edge AI models, including advanced large language models 
            and computer vision technology, to analyze the content you provide. 
            Our system:
          </p>
          <ul>
            <li>Transcribes audio from videos.</li>
            <li>Extracts key claims from text or transcribed audio.</li>
            <li>Analyzes images for context and potential manipulation (where applicable).</li>
            <li>(Optional) Searches the web for corroborating or conflicting information.</li>
            <li>Provides a concise fact-check summary and detailed analysis.</li>
          </ul>

          <h2>Our Technology</h2>
          <p>
            We leverage powerful AI tools, potentially including models from OpenAI and other leading AI research labs, 
            to deliver comprehensive analysis. We continuously strive to improve the accuracy and capabilities 
            of our system.
          </p>

          <h2>Disclaimer</h2>
          <p>
            While we aim for high accuracy, AI-powered fact-checking is a complex 
            field. Results should be considered as a helpful starting point for 
            verification and not as absolute definitive judgments. Always cross-reference 
            with multiple reputable sources.
          </p>
          
          <h2>Contact Us</h2>
          <p>
            Have questions or feedback? Reach out to us:
          </p>
          <ul>
             <li>By email: Info@uygarduzgun</li>
             <li>Website: <a href="https://uygarduzgun.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">uygarduzgun.com</a></li>
             {/* Ensure this is accurate */} 
          </ul>
        </div>
      </div>
    </div>
  );
};

export default About; 