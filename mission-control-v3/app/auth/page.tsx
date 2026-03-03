import { redirect } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

export default async function AuthPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  if (await isAuthenticated()) {
    redirect("/dashboard");
  }

  const params = await searchParams;
  const nextPath = params.next || "/dashboard";

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0a0a0a] px-4">
      <form
        method="post"
        action="/api/auth/login"
        className="w-full max-w-md rounded-lg border border-zinc-800 bg-[#111111] p-6"
      >
        <h1 className="text-xl font-semibold text-zinc-100">Mission Control v3</h1>
        <p className="mt-2 text-sm text-zinc-400">Enter your access token to continue.</p>
        <input type="hidden" name="next" value={nextPath} />
        <label className="mt-5 block text-sm text-zinc-300" htmlFor="token">
          Access token
        </label>
        <input
          id="token"
          name="token"
          type="password"
          required
          className="mt-2 w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500"
        />
        <button
          type="submit"
          className="mt-4 w-full rounded-md border border-zinc-600 bg-zinc-900 px-3 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-800"
        >
          Unlock
        </button>
      </form>
    </main>
  );
}
