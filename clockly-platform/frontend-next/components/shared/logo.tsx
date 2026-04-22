import Image from "next/image";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "white";
}

const heightMap = { sm: 28, md: 36, lg: 48 };

export function Logo({ className, size = "md", variant = "default" }: LogoProps) {
  const h = heightMap[size];
  const src =
    variant === "white"
      ? "/clockly-flow-white.svg"
      : "/clockly-flow-horizontal.svg";

  return (
    <div className={cn("flex items-center", className)}>
      <Image src={src} alt="ClockLy" height={h} width={h * 3.8} priority />
    </div>
  );
}
