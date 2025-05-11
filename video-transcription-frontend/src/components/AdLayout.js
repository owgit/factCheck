import React from 'react';
import AdPlaceholder from './AdPlaceholder';
import SkyscraperAd from './SkyscraperAd';

const AdLayout = ({ children }) => {
  return (
    <div className="ad-layout relative">
      {/* Top Banner Ad */}
      <div className="top-ad-container mb-6 mt-2 flex justify-center">
        <div className="text-center">
          <AdPlaceholder type="leaderboard" className="w-full max-w-screen-xl" />
          <p className="text-xs text-center text-gray-400 mt-2">Advertisement</p>
        </div>
      </div>
      
      {/* Left Skyscraper */}
      <SkyscraperAd side="left" className="xl:left-2 2xl:left-10" />
      
      {/* Main Content */}
      <div className="main-content-with-ads justify-center mx-auto lg:pl-40 lg:pr-40 xl:pl-44 xl:pr-44 2xl:pl-48 2xl:pr-48 px-4">
        {/* Main Content */}
        <div className="flex-grow max-w-6xl mx-auto">
          {children}
        </div>
      </div>
      
      {/* Right Skyscraper */}
      <SkyscraperAd side="right" className="xl:right-2 2xl:right-10" />
      
      {/* Bottom Banner Ad */}
      <div className="bottom-ad-container mt-10 mb-6 flex justify-center">
        <div className="text-center">
          <AdPlaceholder type="leaderboard" className="w-full max-w-screen-xl" />
          <p className="text-xs text-center text-gray-400 mt-2">Advertisement</p>
        </div>
      </div>
    </div>
  );
};

export default AdLayout; 