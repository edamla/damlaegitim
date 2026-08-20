/**
 * Öğretmen wizard → Google Sheets
 * Dağıtım: Execute as Me, Who has access: Anyone
 *
 * Script Properties:
 *   NOTIFY_EMAIL — virgülle ayrılmış alıcılar
 *   RECAPTCHA_SECRET — reCAPTCHA v2 secret key (site key _config.yml'de)
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

function notifyTeam_(data) {
  var recipients = PropertiesService.getScriptProperties().getProperty('NOTIFY_EMAIL');
  if (!recipients) return;
  var subject = 'Yeni öğretmen talebi: ' + (data.okul_adi || '');
  var body = [
    'Ad Soyad: ' + data.ad + ' ' + data.soyad,
    'Okul: ' + data.okul_adi,
    'Sınıf: ' + data.sinif,
    'Ürün sayısı: ' + data.urun_sayisi,
    'Ürünler: ' + data.urun_basliklari,
    'Kaynak: ' + data.kaynak_url
  ].join('\n');
  MailApp.sendEmail(recipients, subject, body);
}
