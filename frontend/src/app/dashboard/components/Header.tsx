"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  return (
    <header className="w-full bg-blue-600 text-white px-6 py-3 flex items-center justify-between shadow">
      <h1 className="text-xl font-bold">TradingAI Dashboard</h1>

      <nav className="flex gap-4">
        <Link href="/dashboard" className="hover:underline">
          Followed
        </Link>
        <Link href="/dashboard" className="hover:underline">
          Invested
        </Link>
        <button
          onClick={logout}
          className="bg-blue-500 hover:bg-blue-700 px-3 py-1 rounded"
        >
          Logout
        </button>
      </nav>
    </header>
  );
}
