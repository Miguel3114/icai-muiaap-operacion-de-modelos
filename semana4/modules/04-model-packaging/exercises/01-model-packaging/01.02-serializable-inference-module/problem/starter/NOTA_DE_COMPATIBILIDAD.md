- Si cambia `preprocessing_version`, se bloquea la carga porque el modelo
  podría recibir datos transformados de una forma distinta a la usada
  durante el entrenamiento.

- Si cambia el orden de `feature_names`, se bloquea la carga porque el
  modelo podría asociar los valores a características incorrectas.