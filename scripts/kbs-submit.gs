/**
 * Kitapla Büyüyen Sınıflar wizard → Google Sheets
 * Dağıtım: Execute as Me, Who has access: Anyone
 *
 * Script Properties:
 *   NOTIFY_EMAIL — virgülle ayrılmış alıcılar
 *   RECAPTCHA_SECRET — reCAPTCHA v2 secret key (site key _config.yml'de)
 */
var BASVURULAR_SHEET = 'Basvurular';

var BASVURULAR_HEADERS = [
  'basvuru_id', 'gonderim_zamani', 'ad', 'soyad', 'okul_adi', 'il', 'ilce',
  'branslar', 'siniflar', 'telefon', 'eposta', 'whatsapp', 'instagram', 'x_hesabi',
  'kvkk_onay', 'kaynak_url', 'user_agent'
];

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
    data.user_agent = normalizeUserAgent_(data.user_agent);
    appendBasvuruRow_(data);
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

function normalizeUserAgent_(raw) {
  var s = raw === null || raw === undefined ? '' : String(raw).trim();
  if (s.length > 45000) return s.substring(0, 45000) + '…';
  return s;
}

function appendBasvuruRow_(data) {
  var sheet = getOrCreateSheet_(BASVURULAR_SHEET, BASVURULAR_HEADERS);
  var row = BASVURULAR_HEADERS.map(function(h) {
    if (h === 'gonderim_zamani') return data.gonderim_zamani || new Date();
    if (h === 'kvkk_onay') return data.kvkk_onay === true || data.kvkk_onay === 'Evet' ? 'Evet' : '';
    if (h === 'user_agent') return normalizeUserAgent_(data.user_agent);
    return data[h] !== undefined ? data[h] : '';
  });
  sheet.appendRow(row);
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

function buildNotifyPlain_(data) {
  var lines = [
    'YENİ KİTAPLA BÜYÜYEN SINIFLAR BAŞVURUSU',
    'Başvuru no: ' + (data.basvuru_id || '—'),
    '',
    'Ad Soyad: ' + data.ad + ' ' + data.soyad,
    'Okul: ' + data.okul_adi,
    'Branş: ' + (data.branslar || '—'),
    'Sınıf: ' + (data.siniflar || '—'),
    'Konum: ' + data.il + ' / ' + data.ilce,
    'Telefon: ' + data.telefon,
    'E-posta: ' + data.eposta,
    ''
  ];
  if (data.whatsapp) lines.push('WhatsApp: ' + data.whatsapp);
  if (data.instagram) lines.push('Instagram: ' + data.instagram);
  if (data.x_hesabi) lines.push('X: ' + data.x_hesabi);
  if (data.user_agent) lines.push('', 'Cihaz (KVKK onay): ' + data.user_agent);
  lines.push('', 'Kaynak: ' + data.kaynak_url);
  return lines.join('\n');
}

function buildNotifyHtml_(data) {
  var when = data.gonderim_zamani
    ? Utilities.formatDate(new Date(data.gonderim_zamani), 'Europe/Istanbul', 'dd.MM.yyyy HH:mm')
    : '—';
  var socialRows = '';
  if (data.whatsapp) socialRows += rowHtml_('WhatsApp', escapeHtml_(data.whatsapp));
  if (data.instagram) socialRows += rowHtml_('Instagram', escapeHtml_(data.instagram));
  if (data.x_hesabi) socialRows += rowHtml_('X', escapeHtml_(data.x_hesabi), !data.whatsapp && !data.instagram);

  return '<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:#f3f6f5;font-family:Segoe UI,Arial,sans-serif;color:#1f2937;">' +
    '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6f5;padding:24px 12px;">' +
    '<tr><td align="center">' +
    '<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;background:#ffffff;border:1px solid #e3efe9;border-radius:12px;overflow:hidden;">' +
    '<tr><td style="background:linear-gradient(135deg,#03a87c,#028a66);padding:20px 24px;">' +
      '<p style="margin:0 0 4px;font-size:12px;letter-spacing:0.06em;text-transform:uppercase;color:rgba(255,255,255,0.85);">Damla Okul</p>' +
      '<h1 style="margin:0;font-size:20px;font-weight:700;color:#ffffff;line-height:1.3;">Kitapla Büyüyen Sınıflar başvurusu</h1>' +
      '<p style="margin:8px 0 0;font-size:13px;color:rgba(255,255,255,0.9);">' + escapeHtml_(data.okul_adi || '') + '</p>' +
    '</td></tr>' +
    '<tr><td style="padding:16px 24px 0;font-size:12px;color:#6b7280;">' +
      'Başvuru no: <strong style="color:#374151;">' + escapeHtml_(data.basvuru_id || '—') + '</strong>' +
      ' &nbsp;·&nbsp; ' + escapeHtml_(when) +
    '</td></tr>' +
    '<tr><td style="padding:16px 24px 20px;">' +
      '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e3efe9;border-radius:8px;overflow:hidden;">' +
        '<tr><td colspan="2" style="padding:10px 14px;background:#f8fbf9;font-size:12px;font-weight:700;color:#03543f;text-transform:uppercase;letter-spacing:0.04em;">Başvuru bilgileri</td></tr>' +
        rowHtml_('Ad Soyad', escapeHtml_(data.ad) + ' ' + escapeHtml_(data.soyad)) +
        rowHtml_('Okul', escapeHtml_(data.okul_adi)) +
        rowHtml_('Branş', escapeHtml_(data.branslar || '—')) +
        rowHtml_('Sınıf', escapeHtml_(data.siniflar || '—')) +
        rowHtml_('Konum', escapeHtml_(data.il) + ' / ' + escapeHtml_(data.ilce)) +
        rowHtml_('Telefon', '<a href="tel:' + escapeHtml_(String(data.telefon || '').replace(/\s/g, '')) + '" style="color:#03543f;text-decoration:none;">' + escapeHtml_(data.telefon) + '</a>') +
        rowHtml_('E-posta', '<a href="mailto:' + escapeHtml_(data.eposta) + '" style="color:#03543f;text-decoration:none;">' + escapeHtml_(data.eposta) + '</a>', !socialRows) +
        socialRows +
      '</table>' +
    '</td></tr>' +
    '<tr><td style="padding:0 24px 24px;font-size:12px;color:#6b7280;line-height:1.6;">' +
      'Form kaynağı: <a href="' + escapeHtml_(data.kaynak_url || 'https://damlaokul.com/kitapla-buyuyen-siniflar') + '" style="color:#03a87c;">' + escapeHtml_(data.kaynak_url || '') + '</a>' +
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

function notifyTeam_(data) {
  var recipients = PropertiesService.getScriptProperties().getProperty('NOTIFY_EMAIL');
  if (!recipients) return;
  var subject = 'KBS başvurusu: ' + (data.okul_adi || '') + ' — ' + (data.ad || '') + ' ' + (data.soyad || '');
  MailApp.sendEmail({
    to: recipients,
    subject: subject,
    body: buildNotifyPlain_(data),
    htmlBody: buildNotifyHtml_(data),
    name: 'Damla Okul'
  });
}
