import React, { useState } from 'react';
import { Folder, FileCode, ChevronRight, ChevronDown } from 'lucide-react';

export default function FileTree({ item, onSelectFile }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!item) return null;

  if (item.type === 'file') {
    return (
      <div
        onClick={() => onSelectFile(item.path)}
        className="flex items-center gap-2 px-3 py-1 text-xs text-gray-300 hover:bg-gray-800 hover:text-white rounded cursor-pointer transition-colors"
      >
        <FileCode className="w-4 h-4 text-indigo-400 shrink-0" />
        <span className="truncate">{item.name}</span>
      </div>
    );
  }

  return (
    <div>
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2 py-1 text-xs text-gray-400 hover:bg-gray-800 hover:text-gray-200 rounded cursor-pointer transition-colors font-medium"
      >
        {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <Folder className="w-4 h-4 text-amber-500 shrink-0" />
        <span className="truncate">{item.name}</span>
      </div>

      {isOpen && item.children && (
        <div className="pl-4 space-y-0.5 border-l border-gray-800 ml-2 mt-0.5">
          {item.children.map((child, idx) => (
            <FileTree key={idx} item={child} onSelectFile={onSelectFile} />
          ))}
        </div>
      )}
    </div>
  );
}