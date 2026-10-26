/* ライト/ダーク切り替え。初期値（data-theme）は head.html のインラインスクリプトが
 * CSS 適用前に確定させている。ここでは [data-theme-toggle] のクリックで反転し、
 * 選択を localStorage に保存し、canvas 再描画のため themechange を発火する。
 * あわせて <meta name="theme-color"> を現在の --bg に合わせる。 */
(() => {
  const root = document.documentElement;
  const buttons = document.querySelectorAll('[data-theme-toggle]');
  if (!buttons.length) return;

  // 現在のテーマ（属性は head のインラインスクリプトが light/dark で確定済み）。
  const current = () => (root.getAttribute('data-theme') === 'light' ? 'light' : 'dark');

  const meta = document.querySelector('meta[name="theme-color"]');
  function syncPressed(theme) {
    buttons.forEach(b => b.setAttribute('aria-pressed', String(theme === 'light')));
    if (meta) meta.content = getComputedStyle(root).getPropertyValue('--bg').trim();
  }

  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem('contour-theme', theme); } catch (e) { /* 保存不可でも続行 */ }
    syncPressed(theme);
    window.dispatchEvent(new Event('themechange'));
  }

  // 初期表示は aria-pressed と theme-color の同期のみ（保存や再描画はユーザー操作時に行う）。
  syncPressed(current());
  buttons.forEach(b => b.addEventListener('click', () => {
    setTheme(current() === 'light' ? 'dark' : 'light');
  }));
})();
