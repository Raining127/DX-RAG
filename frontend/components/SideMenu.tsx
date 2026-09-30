'use client';

import { Menu } from 'antd';
import type { MenuProps } from 'antd';
import WorkspaceIcon from '@/components/WorkspaceIcon';

const MENU_ENTRIES = [
  { key: 'knowledge-base', label: '知识库管理' },
  { key: 'upload', label: '文件上传' },
  { key: 'qa', label: '知识问答' },
  { key: 'files', label: '文件管理' },
] as const;

export type MenuKey = (typeof MENU_ENTRIES)[number]['key'];

interface SideMenuProps {
  selectedKey: MenuKey;
  onSelect: (key: MenuKey) => void;
}

const menuItems: MenuProps['items'] = MENU_ENTRIES.map((entry) => ({
  key: entry.key,
  label: (
    <span className="side-menu-label">
      <span className="side-menu-icon">
        <WorkspaceIcon name={entry.key} />
      </span>
      <span>{entry.label}</span>
    </span>
  ),
}));

export default function SideMenu({ selectedKey, onSelect }: SideMenuProps) {
  const handleClick: MenuProps['onClick'] = ({ key }) => {
    onSelect(key as MenuKey);
  };

  return (
    <nav aria-label="主要功能">
      <Menu
        className="side-menu"
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey]}
        items={menuItems}
        onClick={handleClick}
      />
    </nav>
  );
}
