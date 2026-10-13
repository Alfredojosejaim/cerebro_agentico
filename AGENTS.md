# AGENTS.md — Manual de Uso del Cerebro Agéntico

> **Lectura obligatoria para cualquier IA que opere sobre esta carpeta.**
> Léelo antes de inspeccionar o crear archivos.

---

## 1. Qué es esto y Arquitectura de Memoria

Un **cerebro agéntico** es una memoria externa en disco, organizada en 6 capas, pensada para que una IA (o varias en distintos proyectos) mantenga contexto persistente, sintetice lo que aprende y mantenga trazabilidad sin saturar la ventana de contexto ni depender de una única sesión.

```
cerebro_agentico/
├── index.md        # Mapa de Contenidos global (MOC) para acceso O(1) de bajo consumo
├── inbox/          # 1. Memoria Sensorial: Entrada cruda, volátil y de un solo uso
├── raw/            # 2. Archivo de Fuentes: Documentos y datos originales inalterables
├── wiki/           # 3. Memoria Semántica: Conocimiento compilado, atómico y reutilizable
├── verdad/         # 4. Invariantes / Axiomas: Hechos inmutables de máxima confianza
├── proyectos/      # 5. Memoria de Trabajo: Proyectos activos (snapshot + entregables)
├── log/            # 6. Memoria Episódica: Bitácora cronológica mensual (append-only)
└── scripts/        # Herramientas CLI de eficiencia (scripts/cerebro.py)
```

> **Principio de neutralidad inicial:** Esta estructura nace vacía de contenido de negocio. Se va llenando con el uso real. No crees carpetas ni notas ficticias "por si acaso".

---

## 2. Protocolo de Recuperación Eficiente (Tiered Retrieval)

Para no malgastar tokens ni hacer lecturas exploratorias a ciegas, sigue estrictamente este orden de consulta:

| Nivel | Recurso | Cuándo consultar | Costo de Tokens |
|---|---|---|---|
| **Tier 0** | `index.md` o `python scripts/cerebro.py status` | **Siempre al inicio:** mapea en 1 lectura qué existe en el cerebro. | Mínimo (~100 tokens) |
| **Tier 1** | `verdad/` | Cuando haya restricciones, convenciones o credenciales involucradas. | Bajo |
| **Tier 2** | `proyectos/<proyecto>/estado.md` | Cuando el usuario pide continuar o evaluar un proyecto activo. | Medio |
| **Tier 3** | `wiki/<tema>.md` | Para consultar conceptos destilados específicos identificados en Tier 0. | Medio |
| **Tier 4** | `raw/` | **Solo si es indispensable** verificar la fuente primaria o cita exacta. | Alto (evitar leer por defecto) |

---

## 3. Las 6 Capas y su Ciclo de Vida

### 1. `inbox/` — Entrada cruda (Buffer sensorial)
- **Qué entra:** Fragmentos de chat, URLs, notas sueltas, archivos recién subidos por el usuario.
- **Vida útil:** Máximo 1 sesión de trabajo. Nada duerme en `inbox/`.
- **Procesamiento:** Clasificar hacia `raw/`, `verdad/`, `wiki/` o `proyectos/<slug>/`, borrar el original de `inbox/` y registrar la acción en `log/`.

### 2. `raw/` — Fuentes originales (Referencia inmutable)
- **Qué entra:** PDFs, capturas, transcripciones, exports, código de terceros.
- **Regla:** Solo lectura. **Nunca se edita** el contenido de estos archivos; solo se referencian desde `wiki/` o `proyectos/`. Se crean subcarpetas temáticas solo cuando haya archivos reales (`raw/apis/`, etc.).

### 3. `wiki/` — Conocimiento compilado (Memoria semántica)
- **Qué entra:** Notas atómicas (un concepto o decisión por nota), síntesis, patrones aprendidos, glosarios.
- **Criterio de autonomía:** Cada nota debe responder *"¿qué sabemos sobre X?"* de forma autocontenida sin requerir abrir `raw/`.
- **Enlazado:** Usar enlaces tipo wiki `[[nombre-nota]]` para interconectar conceptos afines.

### 4. `verdad/` — Hechos inmutables (Axiomas del sistema)
- **Qué entra:** Decisiones arquitectónicas irrevocables, convenciones duras, glosarios canónicos, referencias de acceso.
- **Regla de oro:** **Nada entra ni se modifica en `verdad/` sin confirmación explícita del usuario.** Si dudas de la inmutabilidad de un dato, pertenece a `wiki/`, jamás a `verdad/`.

### 5. `proyectos/` — Trabajo activo (Memoria de trabajo)
- Una subcarpeta por proyecto u objetivo: `proyectos/<slug-corto>/`.
```
proyectos/<nombre-proyecto>/
├── estado.md       # Snapshot vivo: objetivo, qué se hizo, pendientes, bloqueos
├── notas/          # Notas de trabajo del día a día (opcional)
└── entregables/    # Artefactos finales producidos (opcional)
```
- **Higiene:** `estado.md` debe mantenerse conciso (< 100 líneas). Cuando un proyecto concluye, se actualiza su estado a cerrado, se extraen lecciones hacia `wiki/` y se conserva como historial.

### 6. `log/` — Bitácora (Memoria episódica)
- Registro cronológico, append-only, mensual (`log/YYYY-MM.md`).
- **Formato obligatorio:**
  ```text
  YYYY-MM-DD HH:MM — [acción] — descripción breve — (proyecto, si aplica)
  ```
- No registrar micro-pasos triviales; solo decisiones clave, creaciones/movimientos de capas o cierres.

---

## 4. Estándar de Notas y Frontmatter (YAML)

Para que cualquier IA procese notas al instante sin consumir la ventana de contexto completa, toda nota nueva en `verdad/`, `wiki/` o `proyectos/` debe incluir esta cabecera:

```yaml
---
tipo: wiki | verdad | proyecto | guia
tags: [tema1, tema2]
descripcion: Resumen de una línea del contenido de este archivo
actualizado: YYYY-MM-DD
---
```

**Beneficio:** Permite al agente leer solo las primeras 6 líneas de un archivo para determinar relevancia antes de cargar el cuerpo completo.

---

## 5. Herramientas CLI de Eficiencia (`scripts/cerebro.py`)

Para acelerar operaciones comunes y ahorrar tokens, la IA puede ejecutar directamente mediante consola:

| Comando | Función |
|---|---|
| `python scripts/cerebro.py status` | Diagnóstico instantáneo de capas, inbox pendiente y proyectos activos. |
| `python scripts/cerebro.py index` | Regenera `index.md` escaneando frontmatters y títulos. |
| `python scripts/cerebro.py search "término"` | Búsqueda por palabras clave con snippets concisos (evita leer archivos completos). |
| `python scripts/cerebro.py log "acción" "descripción" [-p proyecto]` | Agrega la entrada con timestamp automático al `log/YYYY-MM.md` actual. |
| `python scripts/cerebro.py check` | Audita la higiene del cerebro (inbox sucio, notas sin descripción, proyectos incompletos). |

---

## 6. Reglas Inmutables de Operación

1. **Lee antes de escribir.** Revisa siempre `index.md` o usa `scripts/cerebro.py search` antes de redactar para no duplicar información.
2. **Cada capa tiene un propósito único.** No mezcles borradores en `wiki/` ni guardes fuentes procesadas en `inbox/`.
3. **No inventes contenido ficticio.** La estructura debe reflejar únicamente datos reales del usuario.
4. **Nomenclatura kebab-case:** Todo en minúsculas, con guiones, sin espacios ni tildes en nombres de carpetas y archivos (ej. `gestion-usuarios.md`).
5. **Interconectividad:** Compatible con enlaces wiki `[[nota]]` y metadatos YAML para navegación directa en el IDE o por agentes.
6. **Sincronización:** Cada vez que se cree o elimine una nota en `verdad/`, `wiki/` o un proyecto en `proyectos/`, ejecuta `python scripts/cerebro.py index` para mantener `index.md` al día.

---

## 7. Flujo Típico de una Sesión

1. **Reconocimiento:** Ejecutar `python scripts/cerebro.py status` o leer `index.md`.
2. **Clasificación:** Si hay elementos en `inbox/`, procesarlos a sus respectivas capas y vaciar `inbox/`.
3. **Contexto:** Si la tarea atañe a un proyecto existente, leer `proyectos/<slug>/estado.md`. Si es un nuevo objetivo, crear su carpeta con `estado.md`.
4. **Ejecución:** Desarrollar la tarea siguiendo las invariantes de `verdad/` y el conocimiento de `wiki/`.
5. **Cierre de sesión:**
   - Actualizar `estado.md` del proyecto.
   - Si se generó conocimiento duradero, sintetizarlo en `wiki/` con su frontmatter.
   - Registrar la sesión en la bitácora con `python scripts/cerebro.py log`.
   - Si hubo cambios estructurales, sincronizar el índice con `python scripts/cerebro.py index`.
