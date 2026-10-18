/**
 * Game hub landing page: pick Inference Rally (hedge maze) or San Francisco (real streets).
 * Both are the same game server, NPU models and modes; only the track differs.
 * Keys: 1 / 2 open a game. Titles, taglines and map names come from /api/games when the
 * server is up, so racers.yaml stays the one place games are described.
 */

import '@fontsource/press-start-2p';
import './hub.css';

const cards = [...document.querySelectorAll('.hub-card')];

window.addEventListener('keydown', (event) => {
  const card = cards[Number(event.key) - 1];
  if (card) location.href = card.href;
});

fetch('/api/games')
  .then((response) => (response.ok ? response.json() : null))
  .then((games) => {
    if (!games) return;
    for (const card of cards) {
      const game = games[card.dataset.game];
      if (!game) continue;
      card.querySelector('h2').textContent = game.title.toUpperCase();
      if (game.tagline) card.querySelector('.hub-tagline').textContent = game.tagline;
      // "San Francisco · North Beach" -> "North Beach": the card already says the city.
      const areas = game.areas.map((title) => title.split(' · ').pop());
      if (areas.length) card.querySelector('.hub-detail').textContent = areas.join(' · ');
    }
  })
  .catch(() => {}); // the static text is a fine fallback
