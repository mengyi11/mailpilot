"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

type Theme = "light" | "dark" | "system";

function applyTheme(theme: Theme) {
  const dark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.style.colorScheme = dark ? "dark" : "light";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("mailpilot-theme");
    const preferredTheme: Theme =
      savedTheme === "dark" || savedTheme === "light" || savedTheme === "system"
        ? savedTheme
        : "system";

    applyTheme(preferredTheme);
    const frame = window.requestAnimationFrame(() => setTheme(preferredTheme));

    const syncTheme = (event: Event) => {
      const nextTheme = (event as CustomEvent<Theme>).detail;
      setTheme(nextTheme);
      applyTheme(nextTheme);
    };
    window.addEventListener("mailpilot-theme-change", syncTheme);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("mailpilot-theme-change", syncTheme);
    };
  }, []);

  function toggleTheme() {
    const nextTheme: Theme = document.documentElement.classList.contains("dark")
      ? "light"
      : "dark";
    setTheme(nextTheme);
    applyTheme(nextTheme);
    window.localStorage.setItem("mailpilot-theme", nextTheme);
  }

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "切换到浅色主题" : "切换到深色主题"}
    >
      {theme === "light" ? (
        <Moon aria-hidden="true" />
      ) : (
        <Sun aria-hidden="true" />
      )}
    </Button>
  );
}
