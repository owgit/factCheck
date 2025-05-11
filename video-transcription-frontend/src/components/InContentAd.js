import React from 'react';
import AdPlaceholder from './AdPlaceholder';

const InContentAd = ({ className = '' }) => {
  return (
    <div className={`in-content-ad py-4 my-8 ${className}`}>
      <div className="text-center text-xs text-gray-400 uppercase mb-2">Advertisement</div>
      <div className="flex justify-center">
        <AdPlaceholder type="banner" />
      </div>
    </div>
  );
};

export default InContentAd; 