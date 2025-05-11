import React from 'react';

const AdPlaceholder = ({ type = 'rectangle', className = '' }) => {
  // Ad sizes based on IAB standard formats
  const adSizes = {
    leaderboard: { width: '728px', height: '90px', name: 'Leaderboard' },
    rectangle: { width: '300px', height: '250px', name: 'Medium Rectangle' },
    skyscraper: { width: '160px', height: '600px', name: 'Skyscraper' },
    banner: { width: '468px', height: '60px', name: 'Banner' },
    mobile: { width: '320px', height: '50px', name: 'Mobile' },
    large: { width: '336px', height: '280px', name: 'Large Rectangle' }
  };

  const { width, height, name } = adSizes[type] || adSizes.rectangle;
  
  return (
    <div 
      className={`ad-placeholder bg-gray-100 border border-dashed border-gray-300 rounded-md flex items-center justify-center p-4 mx-auto ${className}`}
      style={{ width, height, maxWidth: '100%' }}
      data-ad-type={type}
    >
      <div className="text-center">
        <p className="text-gray-500 text-sm font-medium">{name} Ad Space</p>
        <p className="text-gray-400 text-xs mt-1">{width} × {height}</p>
      </div>
    </div>
  );
};

export default AdPlaceholder; 