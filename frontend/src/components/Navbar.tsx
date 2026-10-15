/**
 * Navbar component.
 *
 * Minimal top navigation with brand identity, lab status,
 * real-time backend telemetry status, and theme switcher (Daylight / After Hours).
 */

import { useEffect, useState } from "react";
import { getHealth } from "../api/client";
import { useTheme } from "../context/useTheme";

interface NavbarProps {
  onResetToOverview?: () => void;
}

export function Navbar({ onResetToOverview }: NavbarProps) {
  const [health, setHealth] = useState<"idle" | "ok" | "error">("idle");
  const [version, setVersion] = useState<string>("");
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    let mounted = true;
    getHealth()
      .then((res) => {
        if (mounted) {
          setHealth("ok");
          setVersion(res.version);
        }
      })
      .catch(() => {
        if (mounted) setHealth("error");
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="navbar" role="banner">
      <div className="container navbar-inner">
        {/* Brand Group */}
        <div className="navbar-brand-group">
          <a
            className="navbar-brand"
            href="#overview"
            onClick={(e) => {
              e.preventDefault();
              onResetToOverview?.();
            }}
            aria-label="DataTripwire Home"
          >
            <div className="brand-glyph" aria-hidden="true">DT</div>
            <span className="brand-name">
              Data<span>Tripwire</span>
            </span>
          </a>
          <span className="brand-badge">
            Reliability Lab // v0.1
          </span>
        </div>

        {/* Right side controls: Health status & Theme Toggle */}
        <div className="navbar-meta">
          {/* Theme Toggle Button */}
          <button
            id="btn-theme-toggle"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={theme === "light" ? "Switch to dark mode (After Hours)" : "Switch to light mode (Daylight)"}
            title={theme === "light" ? "Switch to dark mode (After Hours)" : "Switch to light mode (Daylight)"}
            type="button"
          >
            <span className="theme-toggle-icon" aria-hidden="true">
              {theme === "light" ? (
                /* Moon Icon */
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              ) : (
                /* Sun Icon */
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              )}
            </span>
            <span className="theme-toggle-label">
              {theme === "light" ? "AFTER HOURS" : "DAYLIGHT"}
            </span>
          </button>

          {/* Backend Status Telemetry */}
          <div className="status-indicator" aria-live="polite">
            <span
              className={`status-dot ${health === "ok" ? "ok" : health === "error" ? "error" : ""}`}
              aria-hidden="true"
            />
            {health === "ok" && <span>ENGINE ONLINE // v{version}</span>}
            {health === "error" && <span style={{ color: "var(--clr-danger)" }}>ENGINE OFFLINE</span>}
            {health === "idle" && <span>CONNECTING...</span>}
          </div>
        </div>
      </div>
    </header>
  );
}
