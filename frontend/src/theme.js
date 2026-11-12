// light/dark mode and the accent color, saved in localStorage

export const ACCENTS = ["indigo", "teal", "purple", "rose"];

export function getTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) {
    return saved;
  }
  // nothing saved yet so use what the computer is set to
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

export function getAccent() {
  return localStorage.getItem("accent") || "indigo";
}

export function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
}

export function setAccent(accent) {
  document.documentElement.setAttribute("data-accent", accent);
  localStorage.setItem("accent", accent);
}

// run once before react starts so the page doesnt flash the wrong color
export function loadTheme() {
  document.documentElement.setAttribute("data-theme", getTheme());
  document.documentElement.setAttribute("data-accent", getAccent());
}
