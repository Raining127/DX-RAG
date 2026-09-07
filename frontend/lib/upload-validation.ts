export const MAX_UPLOAD_SIZE_MB = 50;
export const MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;
export const SUPPORTED_EXTENSIONS = [
  '.txt',
  '.md',
  '.csv',
  '.json',
  '.log',
  '.pdf',
  '.docx',
  '.xlsx',
  '.xlsm',
  '.xltx',
  '.xltm',
] as const;

function getExtension(fileName: string): string {
  const dotIndex = fileName.lastIndexOf('.');
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : '';
}

export function validateUploadFile(
  file: Pick<File, 'name' | 'size'>,
): string | null {
  if (
    !SUPPORTED_EXTENSIONS.includes(
      getExtension(file.name) as (typeof SUPPORTED_EXTENSIONS)[number],
    )
  ) {
    return '文件类型不受支持，请选择 TXT、MD、CSV、JSON、LOG、PDF、DOCX 或 Excel 文件。';
  }

  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return '文件大小超过 50MB 限制。';
  }

  if (file.size === 0) {
    return '不能上传空文件。';
  }

  return null;
}
