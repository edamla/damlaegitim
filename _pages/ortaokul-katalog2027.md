---
title: "Katalog redirect"
description: "Katalog"
layout: page
permalink: "/kataloglar/ortaokul-katalog2027"
footer_show: false
---
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- JavaScript çalışmazsa 5 saniye sonra yönlendir -->
  <meta http-equiv="refresh" content="5;url=https://damlaokul.com/kataloglar/ortaokul-katalogu">

  <title>Yönlendiriliyor...</title>

  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #0f172a;
      color: #fff;
      font-family: Arial, sans-serif;
      text-align: center;
    }

    .box {
      padding: 35px;
    }

    .loader {
      width: 40px;
      height: 40px;
      margin: 0 auto 20px;
      border: 4px solid #334155;
      border-top-color: #38bdf8;
      border-radius: 50%;
      animation: spin .8s linear infinite;
    }

    a {
      color: #38bdf8;
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
  </style>
</head>

<body>

  <div class="box">
    <div class="loader"></div>

    <h2>Yönlendiriliyorsunuz...</h2>

    <p>
      Lütfen bekleyin.
      <span id="counter">5</span> saniye.
    </p>

    <!-- JS tamamen kapalıysa kullanıcı yine manuel gidebilir -->
    <noscript>
      <p>
        Otomatik yönlendirme çalışmazsa
        <a href="https://damlaokul.com/kataloglar/ortaokul-katalogu">buraya tıklayın</a>.
      </p>
    </noscript>
  </div>

  <script>
    const redirectUrl = "https://damlaokul.com/kataloglar/ortaokul-katalogu";
    let seconds = 5;

    const counter = document.getElementById("counter");

    const timer = setInterval(() => {
      seconds--;

      if (counter) {
        counter.textContent = seconds;
      }

      if (seconds <= 0) {
        clearInterval(timer);

        // JS çalışıyorsa anında yönlendir
        window.location.replace(redirectUrl);
      }
    }, 1000);
  </script>

</body>
</html>