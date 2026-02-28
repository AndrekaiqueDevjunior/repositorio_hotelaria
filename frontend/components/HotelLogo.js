import React from 'react';

const HotelLogo = ({ className = '', size = 'md' }) => {
  // Size variants
  const sizeClasses = {
    sm: 'h-16 w-16',
    md: 'h-24 w-24',
    lg: 'h-32 w-32',
  };

  const textSizes = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-3xl',
  };

  const subtextSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className={`relative ${sizeClasses[size]}`}>
        {/* Crown */}
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 z-10">
          <svg 
            width="40" 
            height="40" 
            viewBox="0 0 40 40" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className={`${size === 'sm' ? 'w-8 h-8' : 'w-10 h-10'}`}
          >
            <path 
              d="M20 5L25 15L35 12L28 20L38 30L20 25L2 30L12 20L5 12L15 15L20 5Z" 
              fill="#D4AF37" 
              stroke="#B8860B" 
              strokeWidth="1.5"
            />
          </svg>
        </div>
        
        {/* Shield */}
        <div className="w-full h-full bg-blue-700 rounded-lg flex items-center justify-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-blue-800 opacity-90"></div>
          <span className="text-white font-bold text-2xl z-10">HR</span>
        </div>
      </div>
      
      <div className="text-center mt-3">
        <h1 className={`font-bold text-yellow-600 ${textSizes[size]}`}>HOTEL REAL</h1>
        <p className={`text-gray-600 font-medium ${subtextSizes[size]}`}>CABO FRIO</p>
      </div>
    </div>
  );
};

export default HotelLogo;
