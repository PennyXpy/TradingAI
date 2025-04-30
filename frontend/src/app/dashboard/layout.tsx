import React from "react";
import "../globals.css"; // 确保全局样式一次性引入

// 💡 这是一个 *server component*，只负责布局
export default function DashboardLayout({
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      /* 只需要一个包裹节点；绝不要再写 <html>/<body> */
      <section className="h-full w-full">{children}</section>
    );
  }