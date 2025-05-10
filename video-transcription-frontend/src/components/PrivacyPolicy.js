import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const PrivacyPolicy = () => {
  // Basic SEO - Title update (more advanced SEO might use react-helmet or similar)
  React.useEffect(() => {
    document.title = "Privacy Policy - Fact Check";
  }, []);

  return (
    // Use a container similar to the main app results section
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Back to Home Link - slightly more prominent */}
      <div className="mb-6">
        <Link 
          to="/"
          className="inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-900 group bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded-md transition-colors"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2 text-blue-600 group-hover:text-blue-800" aria-hidden="true" />
          Back to Home
        </Link>
      </div>

      {/* Content Card */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
        <div className="px-6 py-5 border-b border-gray-200">
          <h1 className="text-2xl font-semibold text-gray-800">Privacy Policy</h1>
        </div>
        <div className="p-6 prose prose-lg max-w-none text-gray-700">
          <p>Last updated: {new Date().toLocaleDateString()}</p>
          
          <p>
            This Privacy Policy describes Our policies and procedures on the collection, 
            use and disclosure of Your information when You use the Service and tells 
            You about Your privacy rights and how the law protects You.
          </p>
          
          <p>
            We use Your Personal data to provide and improve the Service. By using the 
            Service, You agree to the collection and use of information in accordance 
            with this Privacy Policy.
          </p>

          <h2>Interpretation and Definitions</h2>
          <p>The words of which the initial letter is capitalized have meanings defined under the following conditions. The following definitions shall have the same meaning regardless of whether they appear in singular or in plural.</p>
          {/* Add detailed definitions as needed */}

          <h2>Collecting and Using Your Personal Data</h2>
          <p>While using Our Service, We may ask You to provide Us with certain personally identifiable information that can be used to contact or identify You. Personally identifiable information may include, but is not limited to, Usage Data.</p>
          {/* Add details on types of data collected and how it's used */}
          
          <h2>Contact Us</h2>
          <p>
            If you have any questions about this Privacy Policy, You can contact us:
          </p>
          <ul>
            <li>By email: Info@uygarduzgun</li> 
            {/* Ensure this is accurate */} 
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy; 