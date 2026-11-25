document.documentElement.classList.add("js");
const menu = document.querySelector(".menu-btn");
const nav = document.getElementById("navigation");
function showMenu(open) {
  nav.classList.toggle("open", open);
  menu.setAttribute("aria-expanded", String(open));
}
menu.addEventListener("click", () => showMenu(menu.getAttribute("aria-expanded") !== "true"));
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && menu.getAttribute("aria-expanded") === "true") {
    showMenu(false);
    menu.focus();
  }
});
for (const consoleView of document.querySelectorAll("[data-console]")) {
  const choices = Array.from(consoleView.querySelectorAll("[data-run]"));
  const panels = Array.from(consoleView.querySelectorAll(".run-panel"));
  function selectRun(id) {
    for (const panel of panels) panel.hidden = panel.id !== id;
    for (const choice of choices) {
      if (choice.hash === "#" + id) choice.setAttribute("aria-current", "true");
      else choice.removeAttribute("aria-current");
    }
  }
  function readLocation() {
    const match = choices.find(choice => choice.hash === location.hash);
    selectRun((match || choices[0]).hash.slice(1));
  }
  for (const choice of choices) choice.addEventListener("click", event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    selectRun(choice.hash.slice(1));
    if (location.hash !== choice.hash) history.pushState(null, "", choice.hash);
  });
  window.addEventListener("popstate", readLocation);
  window.addEventListener("hashchange", readLocation);
  readLocation();
}
