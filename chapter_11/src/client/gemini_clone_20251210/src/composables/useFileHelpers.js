// File validation/formatting logic

/** Check if a message has valid files */
export const hasFiles = (msg) => {
  return !!msg && Array.isArray(msg.files) && msg.files.length > 0
}

/** Check if a file is a valid File/Blob object (script-side validation) */
export const isValidFile = (file) => {
  // Check if file is a File/Blob (works in script scope, not template)
  return file && (file instanceof File || file instanceof Blob || !!file.raw)
}

/** Get safe file name (fallback to 'Unknown File') */
export const getFileName = (file) => {
  return file?.name || 'Unknown File'
}

/** Get safe file size (fallback to 0) */
export const getFileSize = (file) => {
  return file?.size || 0
}

/** Safe URL.createObjectURL (only for valid File/Blob) */
export const getFileUrl = (file) => {
  if (!isValidFile(file)) return ''
  // Use raw file if available (Element Plus upload format)
  const fileToUse = file.raw || file
  try {
    return URL.createObjectURL(fileToUse)
  } catch (e) {
    console.warn('Failed to create object URL:', e)
    return ''
  }
}

/** Format file size (unchanged) */
export const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(2)} KB`
  return `${(bytes / 1048576).toFixed(2)} MB`
}

// ✅ Critical: Export the composable as a NAMED function (matches import)
export const useFileHelpers = () => {
  return {
    hasFiles,
    isValidFile,
    getFileName,
    getFileSize,
    getFileUrl,
    formatFileSize
  }
}