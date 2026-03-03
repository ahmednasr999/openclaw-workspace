export default {
  name: "telegram-ingress-audit",
  description: "Ingress audit placeholder",
  enabledByDefault: true,
  matches() { return false; },
  async run() { return { ok: true }; }
};
