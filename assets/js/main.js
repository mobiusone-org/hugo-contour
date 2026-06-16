/* 全ページ共通の初期化。
 * canvas[data-contour] に等高線を描画する。オプションは data 属性で渡す:
 *   data-color="--bg-rgb"  線色（CSS カスタムプロパティ名 or "r, g, b"）
 *   data-cell="10"         グリッドセルの大きさ (css px)
 * #coords があれば、地形の再生成に合わせて座標表示を更新する。 */
(() => {
  const canvas = document.querySelector('canvas[data-contour]');
  if (!canvas) return;

  const opts = {};
  if (canvas.dataset.color) opts.color = canvas.dataset.color;
  if (canvas.dataset.cell) opts.cell = Number(canvas.dataset.cell);

  const coords = document.getElementById('coords');
  if (coords) {
    opts.onRegenerate = ({ lat, lon }) => {
      coords.textContent = Contour.formatCoords(lat, lon);
    };
  }

  Contour.create(canvas, opts);
})();
