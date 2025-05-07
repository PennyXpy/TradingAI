"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function DashboardRedirect() {
  const router = useRouter();
  
  useEffect(() => {
    const redirectUser = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          router.push("/");
          return;
        }
        
        const response = await api.get("/auth/me");
        const username = response.data.username;
        router.push(`/${username}/dashboard`);
      } catch (error) {
        console.error("重定向失败:", error);
        localStorage.removeItem("token");
        router.push("/");
      }
    };
    
    redirectUser();
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin h-10 w-10 border-4 border-blue-500 rounded-full border-t-transparent"></div>
    </div>
  );
}