// Skeletons de chargement.

export const Skeleton = ({ width, height = 16, radius = 8, style: s, count = 1 }) => {
  const base = { width: width || '100%', height, borderRadius: radius, ...s };
  if (count === 1) return <div className="skeleton" style={base} />;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {Array.from({ length: count }, (_, i) => <div key={i} className="skeleton" style={base} />)}
    </div>
  );
};

export const SkeletonRow = ({ cols = 4 }) => (
  <div style={{ display: 'flex', gap: 16, padding: '12px 16px' }}>
    {Array.from({ length: cols }, (_, i) => (
      <div key={i} className="skeleton" style={{ flex: i === 0 ? 2 : 1, height: 14, borderRadius: 6 }} />
    ))}
  </div>
);

export const SkeletonCard = () => (
  <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
    <div className="skeleton" style={{ width: '40%', height: 14, borderRadius: 6 }} />
    <div className="skeleton" style={{ width: '100%', height: 40, borderRadius: 8 }} />
    <div className="skeleton" style={{ width: '70%', height: 14, borderRadius: 6 }} />
  </div>
);
