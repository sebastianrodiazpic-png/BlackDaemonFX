"""Servicios transversales de apoyo al motor.

    - `execution_preflight_service`: comprobaciones previas al envio de orden.
    - `financial_news_service`: calendario de noticias de alto impacto que
      bloquea la apertura de nuevas operaciones en Forex.
    - `live_demo_smoke_test_service`: prueba de humo de extremo a extremo.

Ninguno de estos servicios cierra posiciones abiertas: solo pueden impedir que
se abran nuevas.
"""
