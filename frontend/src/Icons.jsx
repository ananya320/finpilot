const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round", viewBox: "0 0 24 24" };
const make = (d) => ({ size = 20 }) => <svg {...base} width={size} height={size}>{d}</svg>;

export const Home = make(<path d="M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10" />);
export const List = make(<><rect x="4" y="3" width="16" height="18" rx="2" /><path d="M8 8h8M8 12h8M8 16h5" /></>);
export const Sync = make(<><path d="M20 11a8 8 0 0 0-14-4L4 9M4 4v5h5" /><path d="M4 13a8 8 0 0 0 14 4l2-2M20 20v-5h-5" /></>);
export const Sparkle = make(<path d="M12 3l2.2 6.3L21 12l-6.8 2.7L12 21l-2.2-6.3L3 12l6.8-2.7z" />);
export const Cloud = make(<><path d="M7 18a4.5 4.5 0 0 1-.6-8.96A6 6 0 0 1 18 9.5 4 4 0 0 1 17.5 18" /><path d="M12 12v7M9 15l3-3 3 3" /></>);
export const Check = make(<path d="M5 12.5l4.5 4.5L19 7.5" />);
export const Gear = make(<><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" /></>);
export const Logout = make(<><path d="M9 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h4" /><path d="M16 8l4 4-4 4M20 12H9" /></>);
export const Bank = make(<path d="M3 9l9-6 9 6M5 9v9M9.5 9v9M14.5 9v9M19 9v9M3 21h18" />);
export const Doc = make(<><path d="M6 3h8l5 5v13H6z" /><path d="M14 3v5h5M9 13h7M9 17h5" /></>);
export const Card = make(<><rect x="3" y="6" width="18" height="12" rx="2" /><path d="M3 10h18M7 15h4" /></>);
export const Folder = make(<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />);
export const Arrow = make(<path d="M5 12h14M13 6l6 6-6 6" />);
export const Sun = make(<><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5" /></>);
export const Moon = make(<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" />);
export const FileUp = make(<><path d="M6 3h8l5 5v13H6z" /><path d="M14 3v5h5M12 18v-6M9.5 14.5L12 12l2.5 2.5" /></>);
export const Trend = make(<path d="M3 17l6-6 4 4 8-8M15 7h6v6" />);
export const Chevron = make(<path d="M6 9l6 6 6-6" />);

export function Logo({ size = 34 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 34 34">
      <defs>
        <linearGradient id="lg" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#6d4aff" /><stop offset="1" stopColor="#a78bfa" />
        </linearGradient>
      </defs>
      <rect x="2" y="18" width="7" height="14" rx="1.5" fill="url(#lg)" />
      <rect x="13" y="10" width="7" height="22" rx="1.5" fill="url(#lg)" />
      <rect x="24" y="2" width="7" height="30" rx="1.5" fill="url(#lg)" />
    </svg>
  );
}