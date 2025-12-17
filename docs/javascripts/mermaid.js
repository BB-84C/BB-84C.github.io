/* global mermaid */
(() => {
  if (typeof mermaid === "undefined") return;

  mermaid.initialize({
    startOnLoad: true,
    securityLevel: "strict",
    theme: "default",
  });
})();

