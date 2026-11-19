/* Cookie consent for Google Analytics (Google Consent Mode v2).
   Load it before the GA snippet on every page that runs GA. Styles: .cc-bar in assets/css/site.css. */
(function () {
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = gtag;

  // Google works out the visitor's country: analytics stays off in these until they accept.
  gtag('consent', 'default', {
    analytics_storage: 'denied',
    region: ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE',
      'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE',
      'IS', 'LI', 'NO', 'GB', 'CH']
  });
  // The site runs no ads anywhere.
  gtag('consent', 'default', { ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' });

  var KEY = 'cookie-consent';
  var choice = null;
  try { choice = localStorage.getItem(KEY); } catch (e) {}
  if (choice === 'granted' || choice === 'denied') gtag('consent', 'update', { analytics_storage: choice });
  else choice = null;

  // ponytail: the time zone only decides who sees the bar; the region list above is what blocks cookies.
  var tz = '';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
  var inEurope = /^Europe\//.test(tz) ||
    /^(Atlantic\/(Canary|Madeira|Azores|Faroe|Reykjavik)|Arctic\/Longyearbyen)$/.test(tz);

  function clearGaCookies() {
    var domain = '; domain=.' + location.hostname.replace(/^www\./, '');
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (name.indexOf('_ga') !== 0) return;
      ['', domain].forEach(function (d) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + d;
      });
    });
  }

  function show() {
    if (document.querySelector('.cc-bar')) return;
    var bar = document.createElement('div');
    bar.className = 'cc-bar';
    bar.setAttribute('role', 'region');
    bar.setAttribute('aria-label', 'Cookie consent');
    bar.innerHTML =
      '<p>We use Google Analytics cookies to understand how visitors use this site. ' +
      '<a href="privacy-policy.html#cookies">Privacy policy</a></p>' +
      '<div class="cc-btns"><button type="button" data-cc="denied">Decline</button>' +
      '<button type="button" data-cc="granted">Accept</button></div>';
    bar.addEventListener('click', function (e) {
      var v = e.target.getAttribute('data-cc');
      if (!v) return;
      try { localStorage.setItem(KEY, v); } catch (err) {}
      gtag('consent', 'update', { analytics_storage: v });
      if (v === 'denied') clearGaCookies();
      bar.remove();
    });
    document.body.appendChild(bar);
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!choice && inEurope) show();
    // Any element with data-cc-open (e.g. in the privacy policy) reopens the bar.
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('[data-cc-open]')) { e.preventDefault(); show(); }
    });
  });
})();
