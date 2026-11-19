La API pasa a `2.0.0` porque exigir `X-API-Key` rompe a los clientes anónimos
de la `1.x`: es un cambio incompatible. El front de S7 tiene que enviar la
cabecera `X-API-Key` en cada predicción, tratar el `401` (clave ausente o
inválida) y el `429` (esperar los segundos de `Retry-After`). La clave del
front la guardaría en `.env` o en `st.secrets` del lado servidor, nunca en el
código ni en el navegador.