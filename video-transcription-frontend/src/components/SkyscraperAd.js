import React from 'react';
import AdPlaceholder from './AdPlaceholder';

const SkyscraperAd = ({ side = 'left', className = '' }) => {
  // Determine position classes based on side
  const positionClasses = side === 'left' 
    ? 'fixed left-2 lg:left-4 xl:left-6' 
    : 'fixed right-2 lg:right-4 xl:right-6';

  return (
    <div className={`${positionClasses} top-24 hidden lg:block z-10 ${className}`}>
      <div className="sticky top-24">
        <AdPlaceholder type="skyscraper" />
        <p className="text-xs text-center text-gray-400 mt-2">Advertisement</p>
      </div>
    </div>
  );
};

export default SkyscraperAd; 