const CONFIG = {
  inspireApi: 'https://inspirehep.net/api/literature?size=100&sort=mostrecent&q=authors.full_name%3A%22Baruah%2C%20Rajneil%22',
  inspireProfile: 'https://inspirehep.net/authors/2774379',
  orcid: 'https://orcid.org/0000-0001-9792-5496',
  scholar: 'https://scholar.google.com/citations?user=YZDUItYAAAAJ',
  arxiv: 'https://arxiv.org/search/?searchtype=author&query=Baruah%2C+Rajneil',
  instagram: 'YOUR_INSTAGRAM_URL'
};

const $ = (sel) => document.querySelector(sel);
const esc = (s = '') => String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

function linksMarkup() {
  const links = [
    ['INSPIRE-HEP', CONFIG.inspireProfile],
    ['ORCID', CONFIG.orcid],
    ['Google Scholar', CONFIG.scholar],
    ['arXiv', CONFIG.arxiv],
    ['Instagram', CONFIG.instagram]
  ].filter(([, url]) => url && !url.startsWith('YOUR_'));
  return links.map(([name, url]) => `<a href="${url}" target="_blank" rel="noopener">${esc(name)}</a>`).join('');
}

function profileLinksMarkup() {
  const links = [
    ['INSPIRE-HEP', CONFIG.inspireProfile, 'Publications, citations & author record'],
    ['ORCID', CONFIG.orcid, 'Persistent researcher identifier'],
    ['Google Scholar', CONFIG.scholar, 'Citations and scholarly profile'],
    ['arXiv', CONFIG.arxiv, 'Preprints and recent work'],
    ['Instagram', CONFIG.instagram, 'Personal / informal updates']
  ].filter(([, url]) => url && !url.startsWith('YOUR_'));
  return links.map(([name, url, desc]) => `<a class="profile-link" href="${url}" target="_blank" rel="noopener"><strong>${esc(name)}</strong><span>${esc(desc)}</span></a>`).join('');
}

async function loadJSON(path) {
  const r = await fetch(path, { cache: 'no-store' });
  if (!r.ok) throw new Error(`Could not load ${path}`);
  return r.json();
}

function renderCurrentWork(items) {
  $('#currentWork').innerHTML = items.map(item => `
    <article class="current-card">
      <div class="current-status">${esc(item.status || 'In progress')}</div>
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.description)}</p>
      ${item.meta ? `<div class="current-meta">${esc(item.meta)}</div>` : ''}
    </article>`).join('');
}

function renderTalks(items) {
  $('#talksList').innerHTML = items.map(item => `
    <article class="talk">
      <div class="talk-date">${esc(item.date)}</div>
      <h3>${esc(item.title)}</h3>
      <div class="talk-venue">${esc(item.venue)}</div>
      ${item.link ? `<a href="${item.link}" target="_blank" rel="noopener">View slides ↗</a>` : ''}
    </article>`).join('');
}

function authorMarkup(authors = []) {
  const shown = authors.slice(0, 12);
  const html = shown.map(a => {
    const name = typeof a === 'string' ? a : (a.full_name || a.name || '');
    const isRajneil = /ra[jn]neil\s+baruah/i.test(name) || /baruah,\s*rajneil/i.test(name);
    return isRajneil ? `<strong>${esc(name)}</strong>` : esc(name);
  });
  const suffix = authors.length > 12 ? ', et al.' : '';
  return html.join(', ') + suffix;
}

function renderPublications(data) {
  const items = data.publications || [];
  const grouped = items.slice().sort((a,b) => String(b.date || '').localeCompare(String(a.date || '')));
  $('#publicationsList').innerHTML = grouped.map(p => {
    const links = [];
    if (p.arxiv) links.push(`<a href="https://arxiv.org/abs/${encodeURIComponent(p.arxiv)}" target="_blank" rel="noopener">arXiv</a>`);
    if (p.doi) links.push(`<a href="https://doi.org/${encodeURIComponent(p.doi)}" target="_blank" rel="noopener">DOI</a>`);
    if (p.inspire) links.push(`<a href="${p.inspire}" target="_blank" rel="noopener">INSPIRE</a>`);
    return `<article class="pub">
      <div class="pub-year">${esc((p.date || '').slice(0,4))}</div>
      <div>
        <h3 class="pub-title">${esc(p.title)}</h3>
        <div class="pub-meta">${esc(p.venue || p.type || '')}</div>
        <div class="pub-authors">${authorMarkup(p.authors || [])}</div>
      </div>
      <div class="pub-links">${links.join('')}</div>
    </article>`;
  }).join('');
  const updated = data.generated_at ? new Date(data.generated_at).toLocaleDateString(undefined, {year:'numeric', month:'short', day:'numeric'}) : 'recently';
  $('#syncNote').textContent = `Synced from INSPIRE-HEP · ${updated}`;
}

async function loadPublications() {
  try {
    const data = await loadJSON('data/publications.json');
    renderPublications(data);
  } catch (e) {
    $('#syncNote').textContent = 'Publication feed unavailable; use the INSPIRE-HEP link for the live record.';
    $('#publicationsList').innerHTML = `<div class="pub"><div></div><div><h3 class="pub-title">See the live publication record on INSPIRE-HEP.</h3><div class="pub-meta">${esc(CONFIG.inspireProfile)}</div></div></div>`;
  }
}

async function init() {
  $('#heroLinks').innerHTML = linksMarkup();
  $('#profileLinks').innerHTML = profileLinksMarkup();
  $('#year').textContent = new Date().getFullYear();

  try { renderCurrentWork(await loadJSON('data/current-work.json')); } catch (e) {
    $('#currentWork').innerHTML = '<p class="section-intro">Current projects could not be loaded.</p>';
  }
  try { renderTalks(await loadJSON('data/talks.json')); } catch (e) {
    $('#talksList').innerHTML = '<p class="section-intro">Talk data could not be loaded.</p>';
  }
  await loadPublications();

  const menuToggle = $('#menuToggle');
  const navLinks = $('#navLinks');
  menuToggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(open));
  });
  navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    navLinks.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
  }));
}

document.addEventListener('DOMContentLoaded', init);
