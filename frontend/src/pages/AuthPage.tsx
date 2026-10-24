import { useState, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { CarSilhouette } from "../components/CarSilhouette";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await (mode === "login" ? login(email, password) : register(email, password));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  const demo = (e: string, p: string) => { setMode("login"); setEmail(e); setPassword(p); };

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <section className="hidden flex-col justify-between bg-enamel p-10 text-white dark:text-floor lg:flex">
        <p className="font-display text-2xl font-extrabold">Lotkeeper</p>
        <div>
          <div className="mx-auto mb-8 h-40 max-w-sm"><CarSilhouette color="#F2C230" category="Sedan" /></div>
          <h1 className="max-w-md text-5xl font-extrabold leading-[1.05]">Every car on the lot, counted to the last unit.</h1>
          <p className="mt-4 max-w-md opacity-90">Hold a car for ten minutes, buy it before anyone else can, and see stock change the instant it moves.</p>
        </div>
        <p className="text-sm opacity-75">Inventory for dealerships that never oversell.</p>
      </section>

      <section className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-sm space-y-4">
          <h2 className="text-3xl font-extrabold">{mode === "login" ? "Sign in" : "Create your account"}</h2>
          <label className="block text-sm font-semibold">
            Email
            <input className="field mt-1 font-normal" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="block text-sm font-semibold">
            Password
            <input className="field mt-1 font-normal" type="password" required minLength={8} maxLength={72} autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} />
            {mode === "register" && <span className="mt-1 block text-xs font-normal text-muted">At least 8 characters.</span>}
          </label>
          {error && <p role="alert" className="rounded border border-brake/40 bg-brake/10 px-3 py-2 text-sm text-brake">{error}</p>}
          <button className="btn-primary w-full" disabled={busy}>{busy ? "One moment…" : mode === "login" ? "Sign in" : "Create account"}</button>
          <p className="text-sm text-muted">
            {mode === "login" ? "New here?" : "Already registered?"}{" "}
            <button type="button" className="font-semibold text-enamel underline" onClick={() => { setError(null); setMode(mode === "login" ? "register" : "login"); }}>
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>

          <div className="rounded-lg border border-dashed border-line p-3 text-sm">
            <p className="mb-2 font-semibold">Try the demo</p>
            <div className="flex gap-2">
              <button type="button" className="btn-ghost flex-1 !py-1.5" onClick={() => demo("shopper@demo.com", "shopper12345")}>Shopper</button>
              <button type="button" className="btn-ghost flex-1 !py-1.5" onClick={() => demo("admin@demo.com", "admin12345")}>Admin</button>
            </div>
          </div>
        </form>
      </section>
    </main>
  );
}
