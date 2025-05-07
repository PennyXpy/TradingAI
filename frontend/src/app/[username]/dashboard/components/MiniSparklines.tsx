"use client";

interface Props {
  data: number[];
  positive: boolean;
  width?: number;
  height?: number;
}

export default function MiniSparkline({
  data,
  positive,
  width = 60,
  height = 24,
}: Props) {
  // 增强数据验证，确保data存在且不为空
  if (!data || !Array.isArray(data) || data.length === 0) {
    return null;
  }
  
  const max = Math.max(...data);
  const min = Math.min(...data);
  const scaleY = (n: number) =>
    height - ((n - min) / (max - min || 1)) * height;

  const points = data
    .map((d, i) => `${(i / (data.length - 1)) * width},${scaleY(d)}`)
    .join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={positive ? "#16a34a" : "#dc2626"} // green-600 / red-600
        strokeWidth="1.5"
      />
    </svg>
  );
}