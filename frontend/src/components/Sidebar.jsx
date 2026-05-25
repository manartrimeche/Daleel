import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import DIcon from './DIcon';
import { Avatar } from './UI';
import { useAuth } from '../utils/AuthContext';

const sidebarStyles = {
  sidebar: { width: 'var(--sidebar-width)', height: '100vh', background: 'var(--sidebar-bg)', display: 'flex', flexDirection: 'column', flexShrink: 0, position: 'relative', overflow: 'hidden' },
  pattern: { position: 'absolute', inset: 0, opacity: 0.025, backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 24px, rgba(255,255,255,0.4) 24px, rgba(255,255,255,0.4) 25px)', pointerEvents: 'none' },
  nav: { flex: 1, overflowY: 'auto', padding: '20px 12px', position: 'relative', zIndex: 1 },
  groupLabel: { fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'rgba(255,255,255,0.3)', padding: '12px 12px 6px', marginTop: 8 },
  item: { display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontSize: 13, fontWeight: 400, color: 'var(--sidebar-text)', transition: 'all .12s', border: 'none', width: '100%', textAlign: 'left', background: 'none' },
  itemActive: { background: 'var(--sidebar-active)', color: 'var(--sidebar-text-active)', fontWeight: 600 },
  itemHover: { background: 'var(--sidebar-hover)' },
  footer: { padding: '16px', borderTop: '1px solid rgba(255,255,255,0.06)', position: 'relative', zIndex: 1 },
  badge: { marginLeft: 'auto', fontSize: 10, fontWeight: 600, background: 'var(--gold)', color: '#fff', borderRadius: 99, padding: '1px 7px', lineHeight: '16px' },
};

export default function Sidebar() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [hovered, setHovered] = useState(null);
  const userRole = user?.role || 'member';

  const navSections = [
    {
      labelKey: 'sidebar.principal',
      items: [
        { id: 'dashboard', icon: 'grid', labelKey: 'sidebar.dashboard', path: '/dashboard' },
        { id: 'chat', icon: 'messageCircle', labelKey: 'sidebar.assistant', path: '/chat' },
      ],
    },
    {
      labelKey: 'sidebar.management',
      items: [
        { id: 'documents', icon: 'fileText', labelKey: 'sidebar.documents', path: '/admin/documents', roles: ['super_admin', 'owner', 'admin'] },
        { id: 'amendments', icon: 'edit', labelKey: 'sidebar.amendments', path: '/admin/amendments', roles: ['super_admin', 'owner', 'admin'] },
        { id: 'contracts', icon: 'fileSearch', labelKey: 'sidebar.contracts', path: '/admin/contracts', roles: ['super_admin', 'owner', 'admin'] },
        { id: 'cases', icon: 'shieldCheck', labelKey: 'sidebar.cases', path: '/admin/cases', roles: ['owner', 'admin', 'member'] },
        { id: 'history', icon: 'clock', labelKey: 'sidebar.history', path: '/admin/history', roles: ['owner', 'admin'] },
      ],
    },
    {
      labelKey: 'sidebar.administration',
      items: [
        { id: 'company_profile', icon: 'database', labelKey: 'sidebar.companyProfile', path: '/admin/company', roles: ['owner', 'admin'] },
        { id: 'users', icon: 'users', labelKey: 'sidebar.users', path: '/admin/users', roles: ['owner', 'admin'] },
        { id: 'organizations', icon: 'globe', labelKey: 'sidebar.organizations', path: '/admin/organizations', roles: ['super_admin'] },
        { id: 'notifications', icon: 'bell', labelKey: 'sidebar.notifications', path: '/admin/notifications', roles: ['super_admin', 'owner', 'admin', 'member'] },
        { id: 'settings', icon: 'settings', labelKey: 'sidebar.settings', path: '/admin/settings' },
      ],
    },
  ];

  const canSee = (item) => {
    if (!item.roles) return true;
    return item.roles.includes(userRole);
  };

  const isActive = (item) => {
    if (item.path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(item.path);
  };

  return (
    <div style={sidebarStyles.sidebar}>
      <div style={sidebarStyles.pattern} />

      <div style={{ padding: '24px 20px 8px', position: 'relative', zIndex: 1 }}>
        <img
          src="/daleel-logo.svg"
          alt="Daleel"
          style={{
            width: '100%',
            maxWidth: 168,
            height: 72,
            objectFit: 'contain',
            objectPosition: 'left center',
            display: 'block',
          }}
        />
      </div>

      <div style={sidebarStyles.nav}>
        {navSections.map(section => {
          const visibleItems = section.items.filter(canSee);
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.labelKey}>
              <div style={sidebarStyles.groupLabel}>{t(section.labelKey)}</div>
              {visibleItems.map(item => {
                const active = isActive(item);
                const hover = hovered === item.id && !active;
                return (
                  <button
                    key={item.id}
                    onClick={() => navigate(item.path)}
                    onMouseEnter={() => setHovered(item.id)}
                    onMouseLeave={() => setHovered(null)}
                    style={{
                      ...sidebarStyles.item,
                      ...(active ? sidebarStyles.itemActive : {}),
                      ...(hover ? sidebarStyles.itemHover : {}),
                    }}
                  >
                    <DIcon name={item.icon} size={18} />
                    <span>{t(item.labelKey)}</span>
                    {item.badge && <span style={sidebarStyles.badge}>{item.badge}</span>}
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>

      <div style={sidebarStyles.footer}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <Avatar name={user?.full_name || user?.email || 'U'} size={34} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.full_name || user?.email || t('sidebar.defaultUser')}</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.role || t('sidebar.defaultRole')}{user?.organization_name ? ` · ${user.organization_name}` : ''}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
          <button
            onClick={logout}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 6, fontSize: 12, color: 'rgba(255,255,255,0.5)', background: 'none', border: 'none', cursor: 'pointer', transition: 'color .15s' }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--error)'}
            onMouseLeave={e => e.currentTarget.style.color = 'rgba(255,255,255,0.5)'}
          >
            <DIcon name="logout" size={15} />
            {t('sidebar.logout')}
          </button>
        </div>
      </div>
    </div>
  );
}
