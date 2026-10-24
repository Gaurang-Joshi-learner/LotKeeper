/** Stock level shown as a number plate. Yellow = units available; hazard stripes = nothing to sell. */
export function NumberPlate({ available, held }: { available: number; held?: number }) {
  const soldOut = available <= 0;
  return (
    <div
      className={`plate ${soldOut ? "plate-soldout" : ""} flex items-baseline gap-1.5 px-3 py-1 font-display font-extrabold leading-none`}
      aria-label={soldOut ? (held ? "All units on hold" : "Sold out") : `${available} available`}
    >
      {soldOut ? (
        <span className="text-sm tracking-wide">{held ? "ON HOLD" : "SOLD OUT"}</span>
      ) : (
        <>
          <span className="text-2xl">{available}</span>
          <span className="text-xs font-bold">left</span>
        </>
      )}
    </div>
  );
}
