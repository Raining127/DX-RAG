type IconName = 'knowledge-base' | 'upload' | 'qa' | 'files' | 'menu';

const paths: Record<IconName, string> = {
  'knowledge-base': 'M4 4h6v7H4z M14 4h6v7h-6z M4 15h6v5H4z M14 15h6v5h-6z',
  upload: 'M12 16V3 M7 8l5-5 5 5 M4 14v6h16v-6',
  qa: 'M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-6 3V6a2 2 0 0 1 2-2z M8 9h8 M8 13h5',
  files: 'M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z M14 3v6h6 M8 13h8 M8 17h5',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
};

export default function WorkspaceIcon({ name }: { name: IconName }) {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none"
      stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d={paths[name]} />
    </svg>
  );
}
