# DaemonBlackFx v42 — Robustez HTTP

Corrige los tracebacks provocados cuando el navegador cancela una petición del
dashboard mientras Python está enviando la respuesta.

Captura desconexiones esperables:
- BrokenPipeError
- ConnectionResetError
- ConnectionAbortedError
- TimeoutError
- WinError 10053/10054/10057/10058
- EPIPE / ECONNRESET

No modifica SMC, ORB, riesgo, Break Even, TP3/TP4 ni SQLAlchemy.
