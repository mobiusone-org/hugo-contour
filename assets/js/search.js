/* 検索ページ用。/index.json を取得し、依存ライブラリ無しで全文検索する。
 * スペース区切りの語をすべて含む記事（AND）を、出現箇所で重み付けして並べる。
 * URL の ?q= で初期クエリを受け取る（共有・ブックマーク用）。
 *
 * より高機能な検索が必要になったら、ビルド後に索引を作る Pagefind 等への
 * 差し替えを検討する。その場合もこのページ構造（#search-input / #search-results）は流用できる。 */
(() => {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  const count = document.getElementById('search-count');
  if (!input || !results) return;

  let docs = [];
  const ready = fetch(input.dataset.index)
    .then((r) => r.json())
    .then((d) => { docs = d; })
    .catch(() => { docs = []; });

  const escapeHTML = (s) =>
    String(s).replace(/[&<>"]/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  function render(matches, q) {
    results.innerHTML = matches
      .map(
        (m) => `<li>
          <a href="${m.url}">${escapeHTML(m.title)}</a>
          <span class="post-list-date">${escapeHTML(m.date)}</span>
        </li>`
      )
      .join('');
    if (count) {
      count.textContent = q
        ? `${matches.length} result${matches.length === 1 ? '' : 's'}`
        : '';
    }
  }

  function search(q) {
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) { render([], ''); return; }

    const scored = [];
    for (const d of docs) {
      const tags = d.tags || [];
      const hay = `${d.title} ${tags.join(' ')} ${d.summary} ${d.content}`.toLowerCase();
      let score = 0;
      let matchedAll = true;
      for (const t of terms) {
        if (!hay.includes(t)) { matchedAll = false; break; }
        if (d.title.toLowerCase().includes(t)) score += 3;
        if (tags.some((tag) => tag.toLowerCase().includes(t))) score += 2;
        score += 1;
      }
      if (matchedAll) scored.push({ doc: d, score });
    }
    scored.sort((a, b) => b.score - a.score);
    render(scored.map((s) => s.doc), q);
  }

  input.addEventListener('input', () => {
    const q = input.value.trim();
    ready.then(() => search(q));
  });

  const q0 = new URLSearchParams(location.search).get('q');
  if (q0) {
    input.value = q0;
    ready.then(() => search(q0.trim()));
  }
})();
