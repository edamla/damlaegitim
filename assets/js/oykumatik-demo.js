(function(global) {
  var DEMO_QUESTIONS = [
    {
      id: 1,
      text: 'Metinde anlatılan olayın ana fikri aşağıdakilerden hangisidir?',
      options: ['Arkadaşlık önemlidir', 'Hırsızlık yapılmamalıdır', 'Kitap okumak eğlencelidir', 'Spor sağlıklıdır'],
      correct: 0,
      dimension: '1D'
    },
    {
      id: 2,
      text: 'Karakterin duygusal tepkisini en iyi açıklayan seçenek hangisidir?',
      options: ['Kızgınlık', 'Sevinç', 'Korku', 'Merak'],
      correct: 3,
      dimension: '2D'
    },
    {
      id: 3,
      text: 'Yazarın kullandığı benzetme hangi amaca yöneliktir?',
      options: ['Görselleştirme', 'Özetleme', 'Karşılaştırma', 'Tanımlama'],
      correct: 0,
      dimension: '3D'
    },
    {
      id: 4,
      text: 'Metinden çıkarılabilecek en genel yargı hangisidir?',
      options: ['Teknoloji zararlıdır', 'Empati ilişkileri güçlendirir', 'Okul sıkıcıdır', 'Yemek önemlidir'],
      correct: 1,
      dimension: '4D'
    },
    {
      id: 5,
      text: 'Olay örgüsünde doruk noktası hangi bölümde gerçekleşir?',
      options: ['Giriş', 'Gelişme', 'Doruk', 'Sonuç'],
      correct: 2,
      dimension: '1D'
    },
    {
      id: 6,
      text: 'Metindeki ipuçlarına göre karakterin niyeti nedir?',
      options: ['Kaçmak', 'Yardım etmek', 'Saklanmak', 'Alışveriş yapmak'],
      correct: 1,
      dimension: '2D'
    }
  ];

  var DIMENSION_LABELS = {
    '1D': '1D — Bilgi',
    '2D': '2D — Kavrama',
    '3D': '3D — Uygulama',
    '4D': '4D — Analiz'
  };

  function init(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var answers = {};
    var html = '<form id="oyk-demo-form" class="oyk-demo">';
    DEMO_QUESTIONS.forEach(function(q, idx) {
      html += '<fieldset class="oyk-demo__question mb-4"><legend class="h6">' + (idx + 1) + '. ' + escapeHtml(q.text) +
        ' <span class="badge bg-secondary">' + DIMENSION_LABELS[q.dimension] + '</span></legend>';
      q.options.forEach(function(opt, oi) {
        html += '<div class="form-check"><input class="form-check-input" type="radio" name="q' + q.id + '" id="q' + q.id + '_' + oi + '" value="' + oi + '">' +
          '<label class="form-check-label" for="q' + q.id + '_' + oi + '">' + escapeHtml(opt) + '</label></div>';
      });
      html += '</fieldset>';
    });
    html += '<button type="submit" class="btn btn-primary">Sonuçları gör</button></form>';
    html += '<div id="oyk-demo-report" class="mt-4" hidden></div>';
    container.innerHTML = html;

    document.getElementById('oyk-demo-form').addEventListener('submit', function(e) {
      e.preventDefault();
      var results = scoreAnswers();
      renderReport(results);
    });
  }

  function scoreAnswers() {
    var total = DEMO_QUESTIONS.length;
    var correct = 0;
    var byDim = { '1D': { t: 0, c: 0 }, '2D': { t: 0, c: 0 }, '3D': { t: 0, c: 0 }, '4D': { t: 0, c: 0 } };

    DEMO_QUESTIONS.forEach(function(q) {
      var selected = document.querySelector('input[name="q' + q.id + '"]:checked');
      var isCorrect = selected && parseInt(selected.value, 10) === q.correct;
      if (isCorrect) correct++;
      if (byDim[q.dimension]) {
        byDim[q.dimension].t++;
        if (isCorrect) byDim[q.dimension].c++;
      }
    });

    return { total: total, correct: correct, byDim: byDim };
  }

  function renderReport(results) {
    var el = document.getElementById('oyk-demo-report');
    var pct = Math.round((results.correct / results.total) * 100);
    var net = results.correct - (results.total - results.correct) * 0.25;
    net = Math.max(0, Math.round(net * 100) / 100);

    var rows = Object.keys(results.byDim).map(function(dim) {
      var d = results.byDim[dim];
      if (d.t === 0) return '';
      var dp = Math.round((d.c / d.t) * 100);
      return '<tr><td>' + DIMENSION_LABELS[dim] + '</td><td>' + d.c + '/' + d.t + '</td><td>' + dp + '%</td></tr>';
    }).join('');

    el.innerHTML =
      '<div class="oyk-demo-report card border-0 shadow-sm"><div class="card-body">' +
      '<h3 class="h5">Örnek sınıf raporu</h3>' +
      '<p><strong>Doğru:</strong> ' + results.correct + ' / ' + results.total +
      ' &nbsp; <strong>Net:</strong> ' + net + ' &nbsp; <strong>Başarı:</strong> ' + pct + '%</p>' +
      '<table class="table table-sm"><thead><tr><th>Boyut</th><th>Doğru</th><th>Yüzde</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      '<p class="small text-muted mb-0">Bu demo, Dedektif Kuruntusu pilot sorularıyla Öykümatik rapor özetini gösterir.</p>' +
      '</div></div>';
    el.hidden = false;
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  global.OykumatikDemo = { init: init, questions: DEMO_QUESTIONS };
})(window);
