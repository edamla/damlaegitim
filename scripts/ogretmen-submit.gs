/**
 * Öğretmen wizard → Google Sheets
 * Dağıtım: Execute as Me, Who has access: Anyone
 *
 * Script Properties:
 *   NOTIFY_EMAIL — virgülle ayrılmış alıcılar
 *   RECAPTCHA_SECRET — reCAPTCHA v2 secret key (site key _config.yml'de)
 *
 * İlk kurulum — dış ağ izni (reCAPTCHA siteverify için):
 *   1. Editörde izinleriAl fonksiyonunu seç → Çalıştır (▶)
 *   2. İzin isteğinde İncele → Hesabınızla devam → İzin ver
 *   3. Deploy → Manage deployments → New version → Deploy
 */
var TALEPLER_SHEET = 'Talepler';
var URUNLER_SHEET = 'Talep_Urunleri';

var TALEPLER_HEADERS = [
  'talep_id', 'gonderim_zamani', 'sinif', 'ad', 'soyad', 'il', 'ilce',
  'telefon', 'eposta', 'okul_adi', 'urun_sayisi', 'egitim_sayisi', 'hikaye_sayisi',
  'urun_basliklari', 'urun_eanleri', 'urun_sluglari', 'filtre_tur', 'filtre_kategori',
  'filtre_tags', 'filtre_anatemalar', 'filtre_arama', 'kaynak_url'
];

var URUNLER_HEADERS = ['talep_id', 'sira', 'slug', 'baslik', 'ean', 'tur'];

/** Editörden bir kez çalıştırın — UrlFetchApp iznini açar (reCAPTCHA için). */
function izinleriAl() {
  UrlFetchApp.fetch('https://www.google.com/recaptcha/api/siteverify', {
    method: 'post',
    contentType: 'application/x-www-form-urlencoded',
    payload: { secret: 'test', response: 'test' },
    muteHttpExceptions: true
  });
  Logger.log('Tamam. Şimdi Deploy → Manage deployments → New version → Deploy yapın.');
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse_({ ok: false, error: 'empty_body' });
    }
    var data = JSON.parse(e.postData.contents);
    var captcha = verifyRecaptcha_(data.recaptcha_token);
    if (!captcha.ok) {
      return jsonResponse_({ ok: false, error: 'recaptcha', detail: captcha.detail || '' });
    }
    data.gonderim_zamani = new Date();
    appendTalepRow_(data);
    appendUrunRows_(data);
    try {
      notifyTeam_(data);
    } catch (mailErr) {
      // Sheet kaydı başarılı; mail hatası gönderimi iptal etmesin
    }
    return jsonResponse_({ ok: true });
  } catch (err) {
    return jsonResponse_({ ok: false, error: String(err.message || err) });
  }
}

function verifyRecaptcha_(token) {
  var secret = PropertiesService.getScriptProperties().getProperty('RECAPTCHA_SECRET');
  if (!secret) return { ok: true };
  if (!token) return { ok: false, detail: 'missing_token' };
  var resp = UrlFetchApp.fetch('https://www.google.com/recaptcha/api/siteverify', {
    method: 'post',
    contentType: 'application/x-www-form-urlencoded',
    payload: {
      secret: secret,
      response: token
    },
    muteHttpExceptions: true
  });
  var result = JSON.parse(resp.getContentText());
  var codes = (result['error-codes'] || []).join(',');
  return { ok: result.success === true, detail: codes };
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function appendTalepRow_(data) {
  var sheet = getOrCreateSheet_(TALEPLER_SHEET, TALEPLER_HEADERS);
  var row = TALEPLER_HEADERS.map(function(h) {
    if (h === 'gonderim_zamani') return data.gonderim_zamani || new Date();
    return data[h] !== undefined ? data[h] : '';
  });
  sheet.appendRow(row);
}

function appendUrunRows_(data) {
  var sheet = getOrCreateSheet_(URUNLER_SHEET, URUNLER_HEADERS);
  var urunler = data.urunler || [];
  urunler.forEach(function(u) {
    sheet.appendRow([
      data.talep_id,
      u.sira,
      u.slug,
      u.baslik,
      u.ean,
      u.tur
    ]);
  });
}

function getOrCreateSheet_(name, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
  } else if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }
  return sheet;
}

function escapeHtml_(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function gradeLabel_(g) {
  if (g === '0' || g === 0) return 'Okul Öncesi';
  if (g === '' || g === null || g === undefined) return '—';
  return String(g) + '. Sınıf';
}

function siteBaseUrl_(kaynakUrl) {
  var m = String(kaynakUrl || '').match(/^(https?:\/\/[^/]+)/);
  return m ? m[1] : 'https://damlaokul.com';
}

function buildNotifyPlain_(data) {
  var lines = [
    'YENİ ÖĞRETMEN TALEBİ',
    'Talep no: ' + (data.talep_id || '—'),
    '',
    'Ad Soyad: ' + data.ad + ' ' + data.soyad,
    'Okul: ' + data.okul_adi,
    'Sınıf: ' + gradeLabel_(data.sinif),
    'Konum: ' + data.il + ' / ' + data.ilce,
    'Telefon: ' + data.telefon,
    'E-posta: ' + data.eposta,
    '',
    'Toplam ürün: ' + data.urun_sayisi + ' (Hikaye: ' + (data.hikaye_sayisi || 0) + ', Eğitim: ' + (data.egitim_sayisi || 0) + ')',
    '',
    'ÜRÜNLER:'
  ];
  (data.urunler || []).forEach(function(u) {
    lines.push(u.sira + '. [' + u.tur + '] ' + u.baslik + (u.ean ? ' (EAN: ' + u.ean + ')' : ''));
  });
  lines.push('', 'Kaynak: ' + data.kaynak_url);
  return lines.join('\n');
}

function buildNotifyHtml_(data) {
  var base = siteBaseUrl_(data.kaynak_url);
  var when = data.gonderim_zamani
    ? Utilities.formatDate(new Date(data.gonderim_zamani), 'Europe/Istanbul', 'dd.MM.yyyy HH:mm')
    : '—';
  var urunler = data.urunler || [];
  var productRows = urunler.map(function(u) {
    var url = base + '/urunler/' + encodeURIComponent(u.slug || '');
    var turColor = (u.tur === 'Eğitim') ? '#0369a1' : '#047857';
    var turBg = (u.tur === 'Eğitim') ? '#e0f2fe' : '#d1fae5';
    return '<tr>' +
      '<td style="padding:10px 8px;border-bottom:1px solid #eef2f0;color:#6b7280;font-size:13px;width:32px;text-align:center;">' + escapeHtml_(u.sira) + '</td>' +
      '<td style="padding:10px 8px;border-bottom:1px solid #eef2f0;font-size:13px;line-height:1.45;">' +
        '<a href="' + escapeHtml_(url) + '" style="color:#03543f;text-decoration:none;font-weight:600;">' + escapeHtml_(u.baslik) + '</a>' +
        (u.ean ? '<br><span style="color:#9ca3af;font-size:11px;">EAN ' + escapeHtml_(u.ean) + '</span>' : '') +
      '</td>' +
      '<td style="padding:10px 8px;border-bottom:1px solid #eef2f0;width:72px;text-align:center;">' +
        '<span style="display:inline-block;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:600;color:' + turColor + ';background:' + turBg + ';">' + escapeHtml_(u.tur) + '</span>' +
      '</td>' +
    '</tr>';
  }).join('');

  if (!productRows) {
    productRows = '<tr><td colspan="3" style="padding:12px;color:#6b7280;font-size:13px;">Ürün listesi boş.</td></tr>';
  }

  return '<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:#f3f6f5;font-family:Segoe UI,Arial,sans-serif;color:#1f2937;">' +
    '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6f5;padding:24px 12px;">' +
    '<tr><td align="center">' +
    '<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;background:#ffffff;border:1px solid #e3efe9;border-radius:12px;overflow:hidden;">' +
    '<tr><td style="background:linear-gradient(135deg,#03a87c,#028a66);padding:20px 24px;">' +
      '<p style="margin:0 0 4px;font-size:12px;letter-spacing:0.06em;text-transform:uppercase;color:rgba(255,255,255,0.85);">Damla Okul</p>' +
      '<h1 style="margin:0;font-size:20px;font-weight:700;color:#ffffff;line-height:1.3;">Yeni öğretmen talebi</h1>' +
      '<p style="margin:8px 0 0;font-size:13px;color:rgba(255,255,255,0.9);">' + escapeHtml_(data.okul_adi || '') + '</p>' +
    '</td></tr>' +
    '<tr><td style="padding:16px 24px 0;font-size:12px;color:#6b7280;">' +
      'Talep no: <strong style="color:#374151;">' + escapeHtml_(data.talep_id || '—') + '</strong>' +
      ' &nbsp;·&nbsp; ' + escapeHtml_(when) +
    '</td></tr>' +
    '<tr><td style="padding:16px 24px 8px;">' +
      '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e3efe9;border-radius:8px;overflow:hidden;">' +
        '<tr><td colspan="2" style="padding:10px 14px;background:#f8fbf9;font-size:12px;font-weight:700;color:#03543f;text-transform:uppercase;letter-spacing:0.04em;">Öğretmen bilgileri</td></tr>' +
        rowHtml_('Ad Soyad', escapeHtml_(data.ad) + ' ' + escapeHtml_(data.soyad)) +
        rowHtml_('Okul', escapeHtml_(data.okul_adi)) +
        rowHtml_('Sınıf', escapeHtml_(gradeLabel_(data.sinif))) +
        rowHtml_('Konum', escapeHtml_(data.il) + ' / ' + escapeHtml_(data.ilce)) +
        rowHtml_('Telefon', '<a href="tel:' + escapeHtml_(String(data.telefon || '').replace(/\s/g, '')) + '" style="color:#03543f;text-decoration:none;">' + escapeHtml_(data.telefon) + '</a>') +
        rowHtml_('E-posta', '<a href="mailto:' + escapeHtml_(data.eposta) + '" style="color:#03543f;text-decoration:none;">' + escapeHtml_(data.eposta) + '</a>', true) +
      '</table>' +
    '</td></tr>' +
    '<tr><td style="padding:8px 24px;">' +
      '<table role="presentation" width="100%" cellspacing="0" cellpadding="0">' +
        '<tr>' +
          statCell_(String(data.urun_sayisi || 0), 'Toplam ürün') +
          statCell_(String(data.hikaye_sayisi || 0), 'Hikaye') +
          statCell_(String(data.egitim_sayisi || 0), 'Eğitim') +
        '</tr>' +
      '</table>' +
    '</td></tr>' +
    '<tr><td style="padding:8px 24px 20px;">' +
      '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e3efe9;border-radius:8px;overflow:hidden;">' +
        '<tr><td colspan="3" style="padding:10px 14px;background:#f8fbf9;font-size:12px;font-weight:700;color:#03543f;text-transform:uppercase;letter-spacing:0.04em;">Talep edilen ürünler</td></tr>' +
        '<tr style="background:#fafafa;">' +
          '<th style="padding:8px;text-align:center;font-size:11px;color:#6b7280;font-weight:600;">#</th>' +
          '<th style="padding:8px;text-align:left;font-size:11px;color:#6b7280;font-weight:600;">Ürün</th>' +
          '<th style="padding:8px;text-align:center;font-size:11px;color:#6b7280;font-weight:600;">Tür</th>' +
        '</tr>' +
        productRows +
      '</table>' +
    '</td></tr>' +
    '<tr><td style="padding:0 24px 24px;font-size:12px;color:#6b7280;line-height:1.6;">' +
      'Form kaynağı: <a href="' + escapeHtml_(data.kaynak_url || base + '/ogretmen') + '" style="color:#03a87c;">' + escapeHtml_(data.kaynak_url || base + '/ogretmen') + '</a>' +
    '</td></tr>' +
    '</table></td></tr></table></body></html>';
}

function rowHtml_(label, value, isLast) {
  var border = isLast ? '' : 'border-bottom:1px solid #eef2f0;';
  return '<tr>' +
    '<td style="padding:10px 14px;width:120px;font-size:12px;color:#6b7280;vertical-align:top;' + border + '">' + escapeHtml_(label) + '</td>' +
    '<td style="padding:10px 14px;font-size:13px;color:#111827;vertical-align:top;' + border + '">' + value + '</td>' +
  '</tr>';
}

function statCell_(value, label) {
  return '<td width="33%" style="padding:6px;">' +
    '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fbf9;border:1px solid #e3efe9;border-radius:8px;text-align:center;">' +
      '<tr><td style="padding:12px 8px 4px;font-size:22px;font-weight:700;color:#03543f;">' + escapeHtml_(value) + '</td></tr>' +
      '<tr><td style="padding:0 8px 12px;font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.04em;">' + escapeHtml_(label) + '</td></tr>' +
    '</table></td>';
}

function notifyTeam_(data) {
  var recipients = PropertiesService.getScriptProperties().getProperty('NOTIFY_EMAIL');
  if (!recipients) return;
  var subject = 'Yeni öğretmen talebi: ' + (data.okul_adi || '') + ' (' + (data.urun_sayisi || 0) + ' ürün)';
  MailApp.sendEmail({
    to: recipients,
    subject: subject,
    body: buildNotifyPlain_(data),
    htmlBody: buildNotifyHtml_(data),
    name: 'Damla Okul'
  });
}
