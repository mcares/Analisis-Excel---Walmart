def construir_prompt_mejorado(fila):
    return f"""
Eres un **analista experto en experiencia de cliente**. Evalúa la siguiente encuesta de NPS de Walmart Chile y entrega un diagnóstico accionable en **JSON**.  
Responde únicamente en español y SOLO con el JSON especificado.

──────────────── Datos de la encuesta ────────────────
• NPS (0-10, donde 9-10 = Promotor, 7-8 = Neutro, 0-6 = Detractor): {fila['NPS']}
• Requerimiento resuelto según lo acordado (Sí/No): {fila['¿Tu requerimiento fue resuelto en base a lo acordado?']}
• Satisfacción con la resolución (1-7): {fila['Satisfacción con resolución']}
• ¿Se cumplió el plazo de resolución? (Sí/No): {fila['Plazo resolución de requerimiento']}
• Nivel de esfuerzo percibido (1-5, 1 = mucho esfuerzo, 5 = sin esfuerzo): {fila['Nivel de esfuerzo cliente']}
• Nº de interacciones necesarias: {fila['Número de interacciones para resolver requerimiento']}
• Tipo de caso: {fila['Tipo']}
• Sub-familia: {fila['Subfamilia']}
• Causa declarada por agente (si existe): {fila['Causa']}
• Comentario libre del cliente: \"{fila['Walmart LTR - Comentario']}\"

──────────────── Tareas ────────────────
1. **Clasifica** la experiencia (Promotor / Neutro / Detractor).  
2. **Identifica** la causa raíz principal de la insatisfacción o satisfacción (máx. 12 palabras).  
3. **Agrupa** la causa en una categoría genérica (p. ej. “Tiempo de respuesta”, “Calidad solución”, “Comunicación”).  
4. **Analiza** el caso: menciona los factores de la encuesta y del comentario que sustentan tu causa (máx. 40 palabras).  
5. **Detecta** la emoción predominante en el texto (p. ej. “frustración”, “alivio”, “alegría”).  
6. **Evalúa** si el caso es recuperable (Sí/No) considerando NPS, emoción y si el requerimiento se resolvió.  
7. **Recomienda** acciones específicas para mejorar la experiencia futura (máx. 50 palabras, tono directivo).  

──────────────── Formato de salida ────────────────
Devuelve **solo** el siguiente JSON, sin comentarios ni texto adicional:  
{{
  "tipo_experiencia": "...",       // Promotor | Neutro | Detractor
  "causa_principal": "...",        // frase breve
  "categoria": "...",              // categoría genérica
  "detalle_analisis": "...",       // explicación breve
  "emocion_detectada": "...",      // emoción
  "es_recuperable": "...",         // Sí | No
  "recomendacion": "..."           // acción concreta
}}
"""
