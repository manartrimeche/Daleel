// Barrel exports — les primitives sont définies dans ./ui/*.
// Les call sites continuent d'importer depuis '../components/UI' sans changement.

/* eslint-disable react-refresh/only-export-components */

export { Badge, Tag, Avatar, FilterChip } from './ui/Display';
export { DCard, StatCard, ProgressBar, ScoreRing, EmptyState } from './ui/Cards';
export { FormField, DetailField, DButton } from './ui/Forms';
export { DTabs, TimelineItem, LangSwitch } from './ui/Navigation';
export { Skeleton, SkeletonRow, SkeletonCard } from './ui/Skeletons';
export { UIProvider, useToast, useConfirm } from './ui/Feedback';
export { MiniLineChart, AreaLineChart, DonutChart, HorizontalBarChart } from './ui/Charts';
