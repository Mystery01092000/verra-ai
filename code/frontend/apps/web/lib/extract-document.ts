// Extract readable text from user-uploaded files (runs in browser)

const TEXT_EXTENSIONS = new Set(['csv', 'txt', 'json']);

function isTextFile(file: File, ext: string): boolean {
  return TEXT_EXTENSIONS.has(ext) || file.type === 'text/csv' || file.type.startsWith('text/');
}

function isExcelFile(ext: string): boolean {
  return ext === 'xlsx' || ext === 'xls';
}

function formatFileSizeKb(bytes: number): string {
  return (bytes / 1024).toFixed(1);
}

async function extractExcelText(file: File): Promise<string> {
  const { read, utils } = await import('xlsx');
  const buffer = await file.arrayBuffer();
  const wb = read(buffer);
  const sheets = wb.SheetNames.map((name) => {
    const ws = wb.Sheets[name];
    return `--- Sheet: ${name} ---\n${utils.sheet_to_csv(ws ?? {})}`;
  });
  return sheets.join('\n\n');
}

function buildFallbackDescription(file: File): string {
  return (
    `[Document: ${file.name} | Type: ${file.type} | Size: ${formatFileSizeKb(file.size)} KB]\n` +
    'Note: For full PDF text extraction, please copy-paste key figures into the chat.'
  );
}

export async function extractDocumentText(file: File): Promise<string> {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';

  if (isTextFile(file, ext)) {
    return file.text();
  }

  if (isExcelFile(ext)) {
    return extractExcelText(file);
  }

  return buildFallbackDescription(file);
}
