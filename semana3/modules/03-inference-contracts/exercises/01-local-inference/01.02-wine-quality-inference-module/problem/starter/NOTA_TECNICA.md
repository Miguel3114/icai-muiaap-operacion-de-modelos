# 1. Responsabilidad de cada módulo

- contracts.py: define los contratos de entrada y salida mediante Pydantic. Valida los tipos de datos, los rangos permitidos y que no existan campos adicionales.

- preprocess.py: transforma los datos validados en un vector numérico con las once características, respetando el orden y excluyendo `sample_id`.

- inference.py: carga el modelo preentrenado desde el archivo `.joblib`, comprueba que sea compatible con las características esperadas y realiza las predicciones.

- predict_file.py: implementa el CLI. Lee el CSV de entrada, valida y procesa las filas, ejecuta las predicciones y genera el CSV de salida con los resultados. Une todos los procesos en un comando de ejecución.

# 2. Decisiones de diseño

Decisión 1: Separar la validación del preprocesado.

Se utiliza Pydantic para validar los datos antes de construir el vector numérico. Esto permite detectar valores incorrectos o columnas inesperadas antes de ejecutar el modelo, separando las responsabilidades de cada módulo.

Decisión 2: Evitar archivos de salida parciales.

El programa procesa y valida todas las filas antes de escribir el CSV de salida. Si alguna fila es inválida, se interrumpe el proceso sin generar un archivo incompleto y solo se genera el archivo cuando todas las filas se hayan validado correctamente.