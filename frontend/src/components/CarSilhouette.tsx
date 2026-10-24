const TALL = new Set(["suv", "truck", "van"]);

/** A side-on car drawn in the vehicle's own colour; SUVs/trucks/vans get a taller roofline. */
export function CarSilhouette({ color, category }: { color: string | null; category: string }) {
  const fill = color ?? "#7a8793";
  const tall = TALL.has(category.toLowerCase());
  const body = tall
    ? "M8 74 V56 Q8 50 16 48 L48 44 L66 20 Q70 16 78 16 H170 Q178 16 182 22 L196 44 L226 50 Q234 52 234 60 V74 Z"
    : "M8 74 V60 Q8 54 16 52 L58 46 L86 26 Q90 22 98 22 H150 Q158 22 164 28 L186 46 L226 52 Q234 54 234 62 V74 Z";
  const glass = tall
    ? "M72 24 H110 V44 H58 Z M118 24 H168 Q173 24 176 29 L186 44 H118 Z"
    : "M92 30 H122 V46 H72 Z M130 30 H150 Q154 30 158 34 L172 46 H130 Z";
  return (
    <svg viewBox="0 0 242 96" className="h-full w-full" role="img" aria-label={`${category} silhouette`}>
      <ellipse cx="121" cy="88" rx="104" ry="5" fill="#000" opacity="0.14" />
      <path d={body} fill={fill} />
      <path d={glass} fill="#0b1114" opacity="0.62" />
      <path d={body} fill="none" stroke="#000" strokeOpacity="0.28" strokeWidth="2" />
      {[62, 182].map((cx) => (
        <g key={cx}>
          <circle cx={cx} cy="74" r="15" fill="#15181b" />
          <circle cx={cx} cy="74" r="7" fill="#c9ccd1" />
        </g>
      ))}
    </svg>
  );
}
