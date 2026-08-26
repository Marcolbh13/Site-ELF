/* ELF Environnement : interactions et animations */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- header ---------- */
  var header = document.querySelector('.site-header');
  var lastY = 0;
  function onScroll() {
    var y = window.scrollY;
    if (header) {
      header.classList.toggle('is-scrolled', y > 24);
      header.classList.toggle('is-hidden',
        y > 420 && y > lastY && !document.body.classList.contains('nav-open'));
    }
    lastY = y;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- menu mobile ---------- */
  var burger = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.site-nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        document.body.classList.remove('nav-open');
        burger.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && document.body.classList.contains('nav-open')) {
        document.body.classList.remove('nav-open');
        burger.setAttribute('aria-expanded', 'false');
        burger.focus();
      }
    });
  }

  /* ---------- apparitions au scroll ---------- */
  var revealables = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- compteurs ---------- */
  function animateCounter(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var decimals = (el.getAttribute('data-count').split('.')[1] || '').length;
    var suffix = el.getAttribute('data-suffix') || '';
    var dur = 1600;
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    if (reduceMotion) {
      el.textContent = target.toFixed(decimals) + suffix;
    } else {
      requestAnimationFrame(step);
    }
  }
  var counters = document.querySelectorAll('[data-count]');
  if ('IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          cio.unobserve(entry.target);
        }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { cio.observe(el); });
  } else {
    counters.forEach(animateCounter);
  }

  /* ---------- halo des cartes au survol ---------- */
  document.querySelectorAll('.card, .machine-card').forEach(function (card) {
    card.addEventListener('pointermove', function (e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
      card.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
    }, { passive: true });
  });

  /* ---------- formulaire de contact (composition d email) ---------- */
  var form = document.getElementById('contact-form');
  if (form) {
    var params = new URLSearchParams(location.search);
    var wanted = params.get('materiel');
    var debut = params.get('debut');
    var fin = params.get('fin');
    if (wanted || debut || fin) {
      var msg = form.elements.message;
      if (msg && !msg.value) {
        var lignes = [];
        if (wanted) {
          lignes.push(wanted === 'maintenance'
            ? 'Demande d’entretien ou de réparation.'
            : 'Matériel souhaité : ' + wanted);
        }
        if (debut || fin) {
          lignes.push('Chantier' + (debut ? ' du ' + debut : '') + (fin ? ' au ' + fin : ''));
        }
        if (lignes.length) msg.value = lignes.join('\n') + '\n\n';
      }
      var sel = form.elements.sujet;
      if (sel && wanted) {
        sel.value = wanted === 'maintenance' ? 'de maintenance'
          : (/recharge|badge|flotte/i.test(wanted) ? 'de recharge' : 'de location');
      }
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var get = function (name) {
        var f = form.elements[name];
        return f ? f.value.trim() : '';
      };
      var objets = {
        'de location': 'Location',
        'de maintenance': 'Maintenance',
        'de conseil électrique': 'Conseil électrique',
        'de recharge': 'Recharge BTP',
        'autre': 'Autre demande'
      };
      var sujetVal = get('sujet') || 'de contact';
      var sujet = (sujetVal === 'autre' ? 'Autre demande' : 'Demande ' + sujetVal) +
        ' : ' + (get('societe') || get('nom'));
      var corps = [
        'Nom : ' + get('nom'),
        'Société : ' + get('societe'),
        'Email : ' + get('email'),
        'Téléphone : ' + get('tel'),
        'Objet : ' + (objets[sujetVal] || sujetVal),
        '',
        get('message')
      ].join('\n');
      var dest = form.getAttribute('data-dest') || 'contact@elf-environnement.fr';
      window.location.href = 'mailto:' + dest +
        '?subject=' + encodeURIComponent(sujet) +
        '&body=' + encodeURIComponent(corps);
      var note = document.getElementById('form-note');
      if (note) {
        note.hidden = false;
        note.textContent = 'Votre logiciel de messagerie va s’ouvrir avec votre demande. Si rien ne s’ouvre, écrivez-nous à ' + dest + '.';
      }
    });
  }

  /* ---------- rail de la visite du parc ---------- */
  var railLinks = document.querySelectorAll('.visite-rail a');
  var stations = document.querySelectorAll('.visite-station');
  if (railLinks.length && stations.length && 'IntersectionObserver' in window) {
    var sio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        railLinks.forEach(function (a) {
          a.classList.toggle('is-active', a.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    stations.forEach(function (s) { sio.observe(s); });
  }

  /* ---------- annee courante ---------- */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
