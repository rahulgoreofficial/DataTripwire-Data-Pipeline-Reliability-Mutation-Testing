/**
 * ThemeContext — Manages application-wide Light / Dark theme state.
 *
 * Supports:
 * - Persistent theme preference in localStorage ('datatripwire-theme')
 * - Automatic detection of OS system preference when no preference is saved
 * - Immediate data-theme attribute updates on <html>
 * - Zero flash of unstyled content
 */

import React, { useEffect, useState } from "react";
import { type Theme, ThemeContext, getInitialTheme, STORAGE_KEY } from "./ThemeContextCore";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    try {
      localStorage.setItem(STORAGE_KEY, newTheme);
    } catch {
      // ignore storage errors
    }
    document.documentElement.setAttribute("data-theme", newTheme);
  };

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  // Sync with OS preference changes if user hasn't explicitly set a stored choice
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);

    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handleMediaChange = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) {
        setTheme(e.matches ? "dark" : "light");
      }
    };

    mql.addEventListener("change", handleMediaChange);
    return () => mql.removeEventListener("change", handleMediaChange);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
