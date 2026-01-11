import { useState } from 'react';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  isLoading: boolean;
  error?: string | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, isLoading, error }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [fileError, setFileError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.txt')) {
      setFileError('❌ Only .txt files are allowed. Please select a WhatsApp chat export file.');
      return false;
    }
    
    // Check file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setFileError('❌ File is too large. Maximum file size is 50MB.');
      return false;
    }
    
    // Check file is not empty
    if (file.size === 0) {
      setFileError('❌ File is empty. Please select a valid WhatsApp chat export.');
      return false;
    }
    
    setFileError(null);
    return true;
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleUpload = () => {
    if (selectedFile && !fileError) {
      onFileUpload(selectedFile);
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>, dragState: boolean) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(dragState);
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    handleDrag(e, false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  return (
    <div 
      className="card shadow-lg border-0 rounded-4"
      style={{
        background: isDragging 
          ? 'linear-gradient(135deg, rgba(0, 188, 212, 0.15) 0%, rgba(0, 150, 136, 0.15) 100%)'
          : 'rgba(255, 255, 255, 0.9)',
        borderRadius: '25px',
        transition: 'all 0.3s ease',
        transform: isDragging ? 'scale(1.02)' : 'scale(1)',
        border: fileError ? '2px solid #dc3545' : 'none'
      }}
    >
      <div 
        className="card-body p-5 text-center"
        onDragEnter={(e) => handleDrag(e, true)}
        onDragLeave={(e) => handleDrag(e, false)}
        onDragOver={(e) => handleDrag(e, true)}
        onDrop={handleDrop}
      >
        <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>📁</div>
        <h3 className="card-title mb-2" style={{ color: '#00695c', fontSize: '1.8rem' }}>
          Upload WhatsApp Chat
        </h3>
        <p className="card-text" style={{ color: '#00897b', fontSize: '1rem' }}>
          {isDragging ? '✨ Drop your file here' : 'Drag & drop a .txt file or click to select'}
        </p>
        
        <input type="file" id="file-upload" className="d-none" accept=".txt" onChange={handleFileChange} />
        <label htmlFor="file-upload" className="btn btn-outline-primary btn-lg mb-4" style={{
          borderColor: '#00897b',
          color: '#00897b',
          borderRadius: '12px',
          fontWeight: 600,
          cursor: 'pointer'
        }}>
          📂 Browse Files
        </label>

        {fileError && (
          <div className="alert alert-danger mb-4 p-3 rounded" style={{ fontSize: '0.95rem' }} role="alert">
            <strong>File Error:</strong> {fileError}
          </div>
        )}
        
        {selectedFile && !fileError && (
          <p className="mt-3 mb-4" style={{ color: '#00897b', fontWeight: 600, fontSize: '1.05rem' }}>
            ✓ Selected: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(2)} KB)
          </p>
        )}

        <div className="d-grid">
          <button 
            className="btn btn-primary btn-lg" 
            onClick={handleUpload} 
            disabled={!selectedFile || isLoading || !!fileError}
            style={{
              borderRadius: '12px',
              fontWeight: 700,
              padding: '0.85rem',
              fontSize: '1.1rem',
              transition: 'all 0.3s ease',
              opacity: (!selectedFile || isLoading || fileError) ? 0.6 : 1
            }}
            title={!selectedFile ? 'Please select a file' : fileError ? 'Fix file error first' : ''}
          >
            {isLoading ? (
              <>
                <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span className="ms-2">Analyzing... Please wait</span>
              </>
            ) : (
              '🚀 Start Analysis'
            )}
          </button>
        </div>

        <div className="mt-4 p-3 rounded" style={{ backgroundColor: '#f0f8f7', fontSize: '0.9rem', color: '#00695c' }}>
          <p className="mb-2"><strong>💡 Tips:</strong></p>
          <ul className="text-start" style={{ paddingLeft: '1.5rem', marginBottom: 0 }}>
            <li>Export your WhatsApp chat (without media)</li>
            <li>File must be in .txt format</li>
            <li>Maximum file size: 50MB</li>
            <li>Analysis results appear in the "Chat Explorer" tab</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
