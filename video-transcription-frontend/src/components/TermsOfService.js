import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

const TermsOfService = () => {
  React.useEffect(() => {
    document.title = "Terms of Service - Fact Check";
  }, []);

  return (
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
          <h1 className="text-2xl font-semibold text-gray-800">Terms of Service</h1>
        </div>
        <div className="p-6 prose prose-lg max-w-none text-gray-700">
          <p>Last updated: {new Date().toLocaleDateString()}</p>
          
          <p>
            Please read these terms and conditions carefully before using Our Service.
          </p>

          <h2>Interpretation and Definitions</h2>
          <p>The words of which the initial letter is capitalized have meanings defined under the following conditions. The following definitions shall have the same meaning regardless of whether they appear in singular or in plural.</p>
          {/* Add detailed definitions as needed */}

          <h2>Acknowledgment</h2>
          <p>
            These are the Terms and Conditions governing the use of this Service and 
            the agreement that operates between You and the Company. These Terms and 
            Conditions set out the rights and obligations of all users regarding the use 
            of the Service.
          </p>
          <p>
            Your access to and use of the Service is conditioned on Your acceptance of 
            and compliance with these Terms and Conditions. These Terms and Conditions 
            apply to all visitors, users and others who access or use the Service.
          </p>

          <h2>User Accounts</h2>
          <p>When You create an account with Us, You must provide Us information that is accurate, complete, and current at all times. Failure to do so constitutes a breach of the Terms, which may result in immediate termination of Your account on Our Service.</p>
          {/* Add more details about account responsibilities */}

          <h2>Termination</h2>
          <p>We may terminate or suspend Your access immediately, without prior notice or liability, for any reason whatsoever, including without limitation if You breach these Terms and Conditions.</p>
          {/* Add details on conditions for termination */}

          <h2>Contact Us</h2>
          <p>
            If you have any questions about these Terms, You can contact us:
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

export default TermsOfService; 