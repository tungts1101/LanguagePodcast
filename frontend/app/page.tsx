"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/hello")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setMessage(data.message))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black font-sans">
      <main className="flex flex-col items-center gap-4 text-center">
        <h1 className="text-2xl font-semibold text-black dark:text-white">
          Backend connectivity test
        </h1>
        {message && (
          <p className="rounded-md bg-green-100 px-4 py-2 text-green-800">
            {message}
          </p>
        )}
        {error && (
          <p className="rounded-md bg-red-100 px-4 py-2 text-red-800">
            Error: {error}
          </p>
        )}
        {!message && !error && (
          <p className="text-zinc-500">Calling /api/hello…</p>
        )}
      </main>
    </div>
  );
}
