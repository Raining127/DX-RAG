'use client';

import { Menu } from 'antd';
import type { MenuProps } from 'antd';

const MENU_ENTRIES = [
  { key: 'knowledge-base', label: '知识库管理', index: '01' },
  { key: 'upload', label: '文件上传', index: '02' },
  { key: 'qa', label: '知识问答', index: '03' },
  { key: 'files', label: '文件管理', index: '04' },
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
      <span className="side-menu-index" aria-hidden="true">
        {entry.index}
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
