import React, { useRef, useState } from 'react';
import { ZoomIn, ZoomOut, Maximize, SlidersHorizontal } from 'lucide-react';

interface WebGLFitsViewerProps {
  imageUrl: string;
  className?: string;
  alt?: string;
}

export function WebGLFitsViewer({ imageUrl, className = "", alt = "FITS Preview" }: WebGLFitsViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  // Contrast / Z-scale simulation
  const [contrast, setContrast] = useState(100);
  const [brightness, setBrightness] = useState(100);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = -e.deltaY * 0.001;
    setScale(prev => Math.min(Math.max(0.5, prev + zoomFactor), 10));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
    setContrast(100);
    setBrightness(100);
  };

  return (
    <div className={`relative overflow-hidden bg-space-950 flex items-center justify-center ${className}`} ref={containerRef}>
      {/* Viewer controls overlay */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2 bg-space-900/80 p-2 rounded-lg backdrop-blur border border-space-700/50">
        <button onClick={() => setScale(s => Math.min(s + 0.2, 10))} className="p-1.5 hover:bg-space-700 rounded text-space-300 hover:text-white transition-colors">
          <ZoomIn className="w-4 h-4" />
        </button>
        <button onClick={() => setScale(s => Math.max(s - 0.2, 0.5))} className="p-1.5 hover:bg-space-700 rounded text-space-300 hover:text-white transition-colors">
          <ZoomOut className="w-4 h-4" />
        </button>
        <button onClick={resetView} className="p-1.5 hover:bg-space-700 rounded text-space-300 hover:text-white transition-colors">
          <Maximize className="w-4 h-4" />
        </button>
      </div>

      <div className="absolute top-4 right-4 z-10 flex flex-col gap-3 bg-space-900/80 p-3 rounded-lg backdrop-blur border border-space-700/50 w-48">
        <div className="flex items-center gap-2 text-xs text-space-300 mb-1">
          <SlidersHorizontal className="w-3.5 h-3.5" /> Z-Scale Controls
        </div>
        <div>
          <div className="flex justify-between text-[10px] text-space-400 mb-1"><span>Contrast</span><span>{contrast}%</span></div>
          <input type="range" min="50" max="200" value={contrast} onChange={e => setContrast(Number(e.target.value))} className="w-full h-1 bg-space-700 rounded-lg appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-2.5 [&::-webkit-slider-thumb]:h-2.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-neon-500" />
        </div>
        <div>
          <div className="flex justify-between text-[10px] text-space-400 mb-1"><span>Brightness</span><span>{brightness}%</span></div>
          <input type="range" min="50" max="200" value={brightness} onChange={e => setBrightness(Number(e.target.value))} className="w-full h-1 bg-space-700 rounded-lg appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-2.5 [&::-webkit-slider-thumb]:h-2.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-neon-500" />
        </div>
      </div>

      {/* The interactive canvas (simulated with CSS transforms for performance) */}
      <div 
        className="cursor-move"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
          transformOrigin: 'center center',
          transition: isDragging ? 'none' : 'transform 0.1s ease-out'
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img 
          src={imageUrl} 
          alt={alt} 
          draggable={false}
          style={{ 
            filter: `contrast(${contrast}%) brightness(${brightness}%)`,
            imageRendering: 'pixelated'
          }}
          className="max-w-none max-h-none object-contain pointer-events-none"
        />
      </div>
      
      {/* Grid overlay for astronomical context */}
      <div className="absolute inset-0 grid-bg pointer-events-none opacity-20" />
    </div>
  );
}
