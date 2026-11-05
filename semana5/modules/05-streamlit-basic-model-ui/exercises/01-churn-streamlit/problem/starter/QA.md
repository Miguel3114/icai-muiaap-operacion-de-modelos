| Caso | Prueba | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| 1. Sin enviar | Modificar los valores del formulario sin pulsar el botón. | No se ejecuta ninguna predicción ni aparece un nuevo resultado. | Sin predicción |
| 2. Riesgo alto | Introducir `(2, 95, 4, False)` y pulsar «Calcular riesgo». | Se muestra la etiqueta de riesgo, el score y la explicación. | Baja probable: 0.95 |
| 3. Riesgo bajo | Introducir `(36, 35, 0, True)` y pulsar «Calcular riesgo». | Se muestra la etiqueta de riesgo, el score y la explicación. | Permanencia probable: 0.05 |
| 4. Nuevo envío | Cambiar los valores después de una predicción y volver a enviar. | El resultado se actualiza únicamente al pulsar el botón. | Permanencia probable: 0.05 ya que se muestra la nueva predicción |

La aplicación separa la interfaz de la lógica de inferencia y sigue el flujo formulario → submit → predicción → resultado.
Este mismo patrón se podrá reutilizar con el modelo Wine, sustituyendo el contrato de entrada y la función de predicción.