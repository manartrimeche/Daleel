import { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AuthProvider, useAuth } from './utils/AuthContext';
import { LangSwitch } from './components/UI';
import { authFetch } from './utils/auth';
import DIcon from './components/DIcon';
import Login from './pages/Login';
import Invite from './pages/Invite';
import ResetPassword from './pages/ResetPassword';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Documents from './pages/admin/Documents';
import Users from './pages/admin/Users';
import Cases from './pages/admin/Cases';
import Amendments from './pages/admin/Amendments';
import History from './pages/admin/History';
import CompanyProfile from './pages/admin/CompanyProfile';
import Organizations from './pages/admin/Organizations';
import Notifications from './pages/admin/Notifications';
import ContractAnalysis from './pages/admin/ContractAnalysis';
import Settings from './pages/admin/Settings';
import Sidebar from './components/Sidebar';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/" replace />;
  return children;
}

function RoleRoute({ roles, children }) {
  const { user } = useAuth();
  if (roles && !roles.includes(user?.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

function HomeRoute() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Landing />;
  return <Navigate to="/dashboard" replace />;
}

function NotificationBell() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const bellRef = useRef(null);

  useEffect(() => {
    if (!user || user.role === 'viewer') return;
    const fetchCount = () => {
      authFetch('/api/v1/notifications/unread-count')
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data) setUnread(data.unread || 0); })
        .catch(() => {
          // Notification previews are non-blocking.
        });
    };
    fetchCount();
    const interval = setInterval(fetchCount, 60000);
    return () => clearInterval(interval);
  }, [user]);

  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event) => {
      if (bellRef.current && !bellRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [open]);

  if (!user || user.role === 'viewer') return null;

  const loadPreview = async () => {
    setLoading(true);
    try {
      const endpoint = user.role === 'super_admin'
        ? '/api/v1/admin/notifications?limit=5'
        : '/api/v1/notifications/mine?limit=5';
      const res = await authFetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
      }
    } catch {
      // Notification previews are non-blocking.
    }
    setLoading(false);
  };

  const toggleMenu = () => {
    const nextOpen = !open;
    setOpen(nextOpen);
    if (nextOpen) loadPreview();
  };

  const goToAll = () => {
    setOpen(false);
    navigate('/admin/notifications');
  };

  const typeIcon = (type) => ({
    amendment_impact: 'layers',
    approval_organization: 'globe',
    approval_invitation: 'mail',
    approval_document: 'fileText',
    approval_amendment: 'fileText',
    subscription_expiring: 'alertTriangle',
  }[type] || 'bell');

  return (
    <div ref={bellRef} style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={toggleMenu}
        aria-label="Notifications"
        aria-expanded={open}
        style={{ position: 'relative', cursor: 'pointer', padding: 6, borderRadius: 8, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', border: 'none', background: open ? 'var(--surface-hover)' : 'transparent' }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
        onMouseLeave={e => e.currentTarget.style.background = open ? 'var(--surface-hover)' : 'transparent'}
      >
        <DIcon name="bell" size={18} style={{ color: 'var(--text-secondary)' }} />
        {unread > 0 && (
          <span style={{
            position: 'absolute', top: 2, right: 2,
            minWidth: 16, height: 16, borderRadius: 8,
            background: '#e74c3c', color: '#fff',
            fontSize: 10, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '0 4px', lineHeight: 1,
          }}>
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          top: 40,
          right: 0,
          width: 340,
          maxWidth: 'calc(100vw - 32px)',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          boxShadow: '0 14px 36px rgba(0,0,0,0.16)',
          zIndex: 300,
          overflow: 'hidden',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, padding: '12px 14px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)' }}>{t('notifications.title')}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('notifications.unread', { count: unread })}</div>
          </div>

          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: 18, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>{t('common.loading')}</div>
            ) : notifications.length === 0 ? (
              <div style={{ padding: 18, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>{t('notifications.noNotifications')}</div>
            ) : notifications.map(n => (
              <div key={n.id || n._id} style={{ display: 'flex', gap: 10, padding: '11px 14px', borderBottom: '1px solid var(--border-subtle)', opacity: n.read ? 0.65 : 1 }}>
                <div style={{ width: 28, height: 28, borderRadius: 8, background: n.read ? 'var(--surface-hover)' : 'var(--gold-bg)', color: n.read ? 'var(--text-muted)' : 'var(--gold)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <DIcon name={typeIcon(n.alert_type)} size={15} />
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: n.read ? 500 : 700, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.title || t('notifications.title')}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, marginTop: 2, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{n.message || ''}</div>
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={goToAll}
            style={{ width: '100%', padding: '11px 14px', border: 'none', borderTop: '1px solid var(--border)', background: 'transparent', color: 'var(--gold)', fontSize: 12, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
          >
            {t('notifications.seeAll')}
            <DIcon name="arrowRight" size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function AppLayout() {
  const location = useLocation();
  const isChat = location.pathname === '/chat';
  const [sidebarHover, setSidebarHover] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', position: 'relative' }}>
      {/* Zone de détection hover bord gauche (chat uniquement) */}
      {isChat && !sidebarHover && (
        <div
          onMouseEnter={() => setSidebarHover(true)}
          style={{ position: 'fixed', top: 0, left: 0, width: 18, height: '100vh', zIndex: 200, cursor: 'pointer' }}
        />
      )}

      {/* Sidebar : toujours visible sauf sur /chat où il apparaît en overlay au hover */}
      {(!isChat || sidebarHover) && (
        <div
          onMouseLeave={() => { if (isChat) setSidebarHover(false); }}
          style={isChat ? {
            position: 'fixed', top: 0, left: 0, height: '100vh', zIndex: 200,
            boxShadow: '4px 0 24px rgba(0,0,0,0.18)',
            animation: 'sidebarSlideIn .2s ease-out',
          } : {}}
        >
          <Sidebar />
        </div>
      )}

      {/* Fond semi-transparent quand sidebar overlay ouvert */}
      {isChat && sidebarHover && (
        <div
          onClick={() => setSidebarHover(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.25)', zIndex: 199, animation: 'fadeIn .15s ease-out' }}
        />
      )}

      <style>{`
        @keyframes sidebarSlideIn { from { transform: translateX(-100%); } to { transform: translateX(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg)' }}>
        {!isChat && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8, padding: '10px 24px', borderBottom: '1px solid var(--border)', background: 'var(--surface)', flexShrink: 0 }}>
            <NotificationBell />
            <LangSwitch />
          </div>
        )}
        <div style={{ flex: 1, overflow: 'auto' }}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/admin/documents" element={<RoleRoute roles={['super_admin','owner','admin']}><Documents /></RoleRoute>} />
          <Route path="/admin/amendments" element={<RoleRoute roles={['super_admin','owner','admin']}><Amendments /></RoleRoute>} />
          <Route path="/admin/contracts" element={<RoleRoute roles={['super_admin','owner','admin']}><ContractAnalysis /></RoleRoute>} />
          <Route path="/admin/cases" element={<RoleRoute roles={['owner','admin','member']}><Cases /></RoleRoute>} />
          <Route path="/admin/history" element={<RoleRoute roles={['owner','admin']}><History /></RoleRoute>} />
          <Route path="/admin/company" element={<RoleRoute roles={['owner','admin']}><CompanyProfile /></RoleRoute>} />
          <Route path="/admin/users" element={<RoleRoute roles={['owner','admin']}><Users /></RoleRoute>} />
          <Route path="/admin/organizations" element={<RoleRoute roles={['super_admin']}><Organizations /></RoleRoute>} />
          <Route path="/admin/notifications" element={<RoleRoute roles={['super_admin','owner','admin','member']}><Notifications /></RoleRoute>} />
          <Route path="/admin/settings" element={<Settings />} />
          <Route path="*" element={
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 16, padding: 40 }}>
              <DIcon name="alertTriangle" size={48} style={{ color: 'var(--text-muted)' }} />
              <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text)', margin: 0 }}>404</h2>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0 }}>Page introuvable</p>
              <a href="/dashboard" style={{ fontSize: 13, color: 'var(--gold)', fontWeight: 600, textDecoration: 'none', marginTop: 8 }}>Retour au tableau de bord</a>
            </div>
          } />
        </Routes>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomeRoute />} />
          <Route path="/login" element={<Login />} />
          <Route path="/invite" element={<Invite />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
