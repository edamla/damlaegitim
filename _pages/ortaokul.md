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

  {% assign siniflar = site.data.dersler.ortaokul.grades %}
  {% assign ortaokul_subjects = site.data.dersler.ortaokul.subjects %}

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
        {% for subject in ortaokul_subjects %}
        {% assign ders = subject.name %}
        {% assign ders_books = site.books | where_exp: "b", "b.ders == ders" | where_exp: "b", "b.categories contains 'Ortaokul'" %}
        {% if ders_books.size > 0 %}
        <tr>
          <th scope="row">{{ ders }}</th>
          {% for sinif in siniflar %}
          {% assign sinif_num = sinif | plus: 0 %}
          {% unless subject.grades contains sinif_num %}
          <td class="text-muted">—</td>
          {% else %}
          {% assign cell_books = site.books | where_exp: "b", "b.grades contains sinif_num" | where_exp: "b", "b.ders == ders" %}
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
          {% endunless %}
          {% endfor %}
        </tr>
        {% endif %}
        {% endfor %}
        <tr>
          <th scope="row">Genel</th>
          {% for sinif in siniflar %}
          {% assign sinif_num = sinif | plus: 0 %}
          {% assign cell_books = site.books | where_exp: "b", "b.grades contains sinif_num" | where_exp: "b", "b.categories contains 'Ortaokul'" %}
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
      </tbody>
    </table>
  </div>

  <p class="mt-4"><a href="{{ site.baseurl }}/urunler" class="btn btn-primary">Tüm ürünleri filtrele</a></p>
</div>
