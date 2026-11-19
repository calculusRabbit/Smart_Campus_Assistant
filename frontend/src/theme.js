// the 3 looks of the app, saved in localStorage
// light = default, dark = dark mode, colorblind = blue/orange colors that work for color blind people

export const THEMES = [
  { id: "light", label: "Light" },
  { id: "dark", label: "Dark" },
  { id: "colorblind", label: "Color-blind" },
];

export function getTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark" || saved === "colorblind") {
    return saved;
  }
  // nothing saved yet so use what the computer is set to
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

export function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
}

// run once before react starts so the page doesnt flash the wrong color
export function loadTheme() {
  document.documentElement.setAttribute("data-theme", getTheme());
}
