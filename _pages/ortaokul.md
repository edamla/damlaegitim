---
title: "Ortaokul Yayınları"
description: "5–8. sınıf Damla Okul eğitim setleri ve hikaye kitapları — sınıf × ders matrisi."
layout: page
permalink: "/ortaokul"
footer_show: true
---

<div class="container py-4">
  <header class="mb-4">
    <h1 class="display-5">Ortaokul (5–8. Sınıf)</h1>
    <p class="lead text-muted">Sınıf ve ders bazında Damla Okul yayınları. LGS hazırlık ve okuma kültürü tek vitrinde.</p>
  </header>

  {% assign dersler = "Türkçe,Matematik,Fen Bilimleri,İnkılap,Sosyal Bilgiler,Din Kültürü ve Ahlak Bilgisi,Genel" | split: "," %}
  {% assign siniflar = "5,6,7,8" | split: "," %}

  <div class="table-responsive">
    <table class="table table-bordered align-middle">
      <thead class="table-light">
        <tr>
          <th scope="col">Ders / Sınıf</th>
          {% for sinif in siniflar %}
          <th scope="col">{{ sinif }}. Sınıf</th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for ders in dersler %}
        <tr>
          <th scope="row">{{ ders }}</th>
          {% for sinif in siniflar %}
          {% assign sinif_num = sinif | plus: 0 %}
          {% assign cell_books = site.books | where_exp: "b", "b.grades contains sinif_num" %}
          {% if ders == "Genel" %}
            {% assign cell_books = cell_books | where_exp: "b", "b.categories contains 'Ortaokul'" %}
          {% else %}
            {% assign cell_books = cell_books | where_exp: "b", "b.categories contains ders" %}
          {% endif %}
          <td>
            {% if cell_books.size > 0 %}
            <ul class="list-unstyled small mb-0">
              {% for book in cell_books limit: 4 %}
              <li><a href="{{ site.baseurl }}{{ book.url }}">{{ book.title }}</a></li>
              {% endfor %}
              {% if cell_books.size > 4 %}
              <li class="text-muted">+{{ cell_books.size | minus: 4 }} ürün</li>
              {% endif %}
            </ul>
            {% else %}
            <span class="text-muted">—</span>
            {% endif %}
          </td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <p class="mt-4"><a href="{{ site.baseurl }}/urunler" class="btn btn-primary">Tüm ürünleri filtrele</a></p>
</div>
