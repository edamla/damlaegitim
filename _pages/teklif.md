---
title: "Okul Programı Teklif Talebi"
description: "Okulunuz için Damla Okul programı teklifi isteyin. Talebiniz 48 saat içinde değerlendirilir."
layout: page
permalink: "/teklif"
footer_show: true
---

<style>
  .teklif-hero {
    background: linear-gradient(135deg, #f4faf7 0%, #fff 100%);
    border: 1px solid #e3efe9;
    border-radius: calc(var(--radius, 0.5rem) * 2);
    padding: 2rem;
    margin-bottom: 2rem;
  }
  .teklif-form-wrap iframe {
    width: 100%;
    min-height: 1400px;
    border: 0;
  }
</style>

<div class="container py-4">
  <section class="teklif-hero">
    <h1 class="display-6">Okul Programı Teklif Talebi</h1>
    <p class="lead text-muted mb-0">
      Okulunuz veya sınıfınız için Damla Okul programı (eğitim seti + hikaye + öğretmen desteği) hakkında teklif almak için formu doldurun.
      Talebiniz yetkili bayimize iletilir; <strong>iş günü içinde 48 saat</strong> içinde sizinle iletişime geçilir.
    </p>
    <p class="mt-2 mb-0 small text-muted">
      Bireysel kitap seçimi için öğretmenler <a href="{{ site.baseurl }}/ogretmen">Öğretmen Köşesi</a> sayfasını kullanabilir.
    </p>
  </section>

  <section aria-labelledby="teklif-form-title">
    <h2 id="teklif-form-title" class="h4 mb-3">Teklif formu</h2>
    {% if site.teklif_form_url and site.teklif_form_url != '' %}
    <div class="teklif-form-wrap">
      <iframe
        src="{{ site.teklif_form_url }}"
        title="Damla Okul okul programı teklif formu"
        width="640"
        height="1400"
        loading="lazy">
        Yükleniyor…
      </iframe>
    </div>
    {% else %}
    <div class="alert alert-info">
      <p class="mb-0">Google Form embed URL’si henüz yapılandırılmadı. Operasyon ekibi formu oluşturduktan sonra <code>_config.yml</code> içindeki <code>teklif_form_url</code> alanına <code>…/viewform?embedded=true</code> adresini ekleyin.</p>
    </div>
    {% endif %}
  </section>
</div>
