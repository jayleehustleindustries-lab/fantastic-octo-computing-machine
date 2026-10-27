const escapeHtml = (text: string) =>
  text.replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]!);

type LoginPageOptions = {
  /** The signed sign-in request; absent when the link has expired. */
  form?: string;
  clientName?: string;
  error?: string;
  expired?: boolean;
};

/** The owner's sign-in page for the Claude connector, in the site's HUD style. No scripts. */
export function loginPage({ form, clientName, error, expired }: LoginPageOptions): string {
  const who = escapeHtml(clientName?.trim() || "Claude");
  const body = expired || !form
    ? `<p class="lead">This sign-in link has expired.</p><p class="muted">Go back to Claude and press Connect again.</p>`
    : `<p class="lead"><strong>${who}</strong> wants access to the JayLee Hustle site: leads, Remap orders, clients and payment reports.</p>
      <form method="post" action="/mcp-login">
        <input type="hidden" name="form" value="${escapeHtml(form)}">
        <label for="password">OWNER PASSWORD</label>
        <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
        ${error ? `<p class="error" role="alert">${escapeHtml(error)}</p>` : ""}
        <button type="submit" name="action" value="allow">ALLOW ACCESS</button>
        <button type="submit" name="action" value="cancel" class="secondary" formnovalidate>CANCEL</button>
      </form>
      <p class="muted">Only the site owner can sign in. Access lasts until you disconnect it in Claude or the signing secret changes.</p>`;

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Connect Claude · JayLee Hustle</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 16px;
    background: radial-gradient(circle at 50% 0%, #0b1a2a 0%, #05070b 60%); color: #e6edf5;
    font: 15px/1.5 ui-monospace, "JetBrains Mono", Menlo, monospace; }
  .card { width: 100%; max-width: 420px; border: 1px solid rgba(56,198,255,.35); background: #0e1218;
    padding: 28px 24px; position: relative; box-shadow: 0 0 40px rgba(56,198,255,.08); }
  .card::before, .card::after { content: ""; position: absolute; width: 14px; height: 14px; border: 2px solid #38c6ff; }
  .card::before { top: -2px; left: -2px; border-right: 0; border-bottom: 0; }
  .card::after { bottom: -2px; right: -2px; border-left: 0; border-top: 0; }
  .tag { font-size: 11px; letter-spacing: .2em; color: #38c6ff; margin: 0 0 6px; }
  h1 { font-size: 22px; letter-spacing: .08em; margin: 0 0 16px; }
  .lead { margin: 0 0 18px; }
  .muted { color: #8b95a5; font-size: 12px; margin: 16px 0 0; }
  label { display: block; font-size: 11px; letter-spacing: .2em; color: #8b95a5; margin-bottom: 6px; }
  input[type=password] { width: 100%; padding: 12px; background: #05070b; color: #e6edf5;
    border: 1px solid rgba(255,255,255,.18); font: inherit; }
  input[type=password]:focus { outline: 2px solid #38c6ff; outline-offset: 1px; }
  button { width: 100%; margin-top: 14px; padding: 12px; font: inherit; letter-spacing: .15em; cursor: pointer;
    background: #38c6ff; color: #05070b; border: 0; font-weight: 700; }
  button.secondary { background: transparent; color: #8b95a5; border: 1px solid rgba(255,255,255,.18); font-weight: 400; }
  .error { color: #ff6b6b; margin: 10px 0 0; }
</style>
</head>
<body>
  <main class="card">
    <p class="tag">MOD-MCP // CONNECT</p>
    <h1>CONNECT CLAUDE</h1>
    ${body}
  </main>
</body>
</html>`;
}
