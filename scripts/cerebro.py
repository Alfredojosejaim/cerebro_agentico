#!/usr/bin/env python3
"""
cerebro.py — Herramienta de eficiencia para el Cerebro Agéntico.

Permite a agentes y usuarios:
- Consultar el estado del cerebro en milisegundos (`status`)
- Reconstruir el mapa de contenidos global (`index`)
- Registrar acciones en la bitácora automáticamente (`log`)
- Buscar contenido relevante con bajo consumo de tokens (`search`)
- Verificar la salud e integridad de la memoria (`check`)
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

# Asegurar codificación utf-8 en terminales Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Raíz del repositorio (directorio padre de scripts/ o directorio actual)
BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent

LAYERS = ["inbox", "raw", "wiki", "verdad", "proyectos", "log"]


def parse_frontmatter(file_path: Path):
    """Extrae metadatos básicos de frontmatter YAML y el primer encabezado Markdown."""
    meta = {"titulo": file_path.stem, "descripcion": "", "tags": [], "tipo": ""}
    if not file_path.exists() or not file_path.is_file():
        return meta

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return meta

    # Primer encabezado H1 si existe
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        meta["titulo"] = h1_match.group(1).strip()

    # Frontmatter YAML delimitado por ---
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.splitlines():
            line = line.strip()
            if line.startswith("descripcion:"):
                meta["descripcion"] = line.split("descripcion:", 1)[1].strip().strip('"\'')
            elif line.startswith("tipo:"):
                meta["tipo"] = line.split("tipo:", 1)[1].strip().strip('"\'')
            elif line.startswith("tags:"):
                raw_tags = line.split("tags:", 1)[1].strip()
                if raw_tags.startswith("[") and raw_tags.endswith("]"):
                    meta["tags"] = [t.strip().strip('"\'') for t in raw_tags[1:-1].split(",") if t.strip()]
                else:
                    meta["tags"] = [raw_tags] if raw_tags else []

    # Si no hay descripción en frontmatter, usar primer párrafo no vacío
    if not meta["descripcion"]:
        body = content[fm_match.end():] if fm_match else content
        for paragraph in body.split("\n\n"):
            p = paragraph.strip()
            if p and not p.startswith("#") and not p.startswith(">") and not p.startswith("```"):
                clean = re.sub(r"\[\[(.*?)\]\]", r"\1", p)
                clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)
                meta["descripcion"] = clean.replace("\n", " ")[:120].strip()
                break

    return meta


def cmd_status(args):
    """Muestra un diagnóstico rápido y compacto del estado del cerebro."""
    print("=== ESTADO DEL CEREBRO AGÉNTICO ===")
    
    # Conteo por capas
    counts = {}
    for layer in LAYERS:
        p = BASE_DIR / layer
        if p.exists() and p.is_dir():
            files = [f for f in p.rglob("*") if f.is_file() and f.name != ".gitkeep"]
            counts[layer] = len(files)
        else:
            counts[layer] = 0

    print(f"Capas: inbox={counts['inbox']} | raw={counts['raw']} | wiki={counts['wiki']} | verdad={counts['verdad']} | proyectos={counts['proyectos']} | logs={counts['log']}")

    # Alerta de inbox
    inbox_files = [f.name for f in (BASE_DIR / "inbox").iterdir() if f.is_file() and f.name != ".gitkeep"]
    if inbox_files:
        print(f"⚠️  INBOX PENDIENTE ({len(inbox_files)}): {', '.join(inbox_files[:5])}")
    else:
        print("✓ Inbox: limpio")

    # Proyectos activos
    proy_dir = BASE_DIR / "proyectos"
    proyectos = []
    if proy_dir.exists():
        for d in proy_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                estado = d / "estado.md"
                has_estado = " (con estado.md)" if estado.exists() else " (sin estado.md)"
                proyectos.append(f"{d.name}{has_estado}")
    if proyectos:
        print(f"Proyectos ({len(proyectos)}): {', '.join(proyectos)}")
    else:
        print("Proyectos: ninguno activo")

    # Última entrada del log
    log_dir = BASE_DIR / "log"
    last_entry = None
    if log_dir.exists():
        log_files = sorted([f for f in log_dir.glob("*.md") if f.is_file()], reverse=True)
        if log_files:
            lines = [l.strip() for l in log_files[0].read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                last_entry = f"[{log_files[0].name}] {lines[-1]}"

    if last_entry:
        print(f"Último log: {last_entry}")
    else:
        print("Último log: sin entradas")


def cmd_index(args):
    """Regenera index.md con el mapa de contenidos actualizado."""
    index_path = BASE_DIR / "index.md"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Índice del Cerebro Agéntico",
        "",
        "> Mapa de contenido (MOC) optimizado para consulta rápida de agentes y desarrolladores.",
        f"> *Última sincronización: {now_str}*",
        "",
        "---",
        "",
        "## 1. Verdad (Hechos Inmutables & Restricciones)",
    ]

    verdad_dir = BASE_DIR / "verdad"
    verdad_files = [f for f in verdad_dir.glob("*.md") if f.is_file()] if verdad_dir.exists() else []
    if verdad_files:
        for f in sorted(verdad_files):
            meta = parse_frontmatter(f)
            desc = f" — {meta['descripcion']}" if meta['descripcion'] else ""
            lines.append(f"- [[verdad/{f.name}|{meta['titulo']}]]`{desc}`")
    else:
        lines.append("*(Sin notas inmutables todavía — requiere confirmación explícita)*")

    lines.extend([
        "",
        "## 2. Proyectos Activos (Memoria de Trabajo)",
    ])

    proy_dir = BASE_DIR / "proyectos"
    proy_folders = [d for d in proy_dir.iterdir() if d.is_dir() and not d.name.startswith(".")] if proy_dir.exists() else []
    if proy_folders:
        for d in sorted(proy_folders):
            estado = d / "estado.md"
            if estado.exists():
                meta = parse_frontmatter(estado)
                desc = f" — {meta['descripcion']}" if meta['descripcion'] else ""
                lines.append(f"- [[proyectos/{d.name}/estado|{d.name}]]`{desc}`")
            else:
                lines.append(f"- `{d.name}/` (sin estado.md)")
    else:
        lines.append("*(Sin proyectos activos actualmente)*")

    lines.extend([
        "",
        "## 3. Wiki (Conocimiento Compilado & Sintetizado)",
    ])

    wiki_dir = BASE_DIR / "wiki"
    wiki_files = [f for f in wiki_dir.glob("*.md") if f.is_file()] if wiki_dir.exists() else []
    if wiki_files:
        for f in sorted(wiki_files):
            meta = parse_frontmatter(f)
            desc = f" — {meta['descripcion']}" if meta['descripcion'] else ""
            tags_str = f" `[{', '.join(meta['tags'])}]`" if meta['tags'] else ""
            lines.append(f"- [[wiki/{f.name}|{meta['titulo']}]]`{desc}`{tags_str}")
    else:
        lines.append("*(Sin notas compiladas todavía)*")

    lines.extend([
        "",
        "## 4. Referencias",
        "- [[AGENTS|Manual AGENTS.md]] — Reglas operativas y arquitectura del cerebro",
        "",
    ])

    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ index.md generado exitosamente en {index_path.name}")


def cmd_log(args):
    """Registra una acción en log/YYYY-MM.md siguiendo la convención estricta."""
    now = datetime.datetime.now()
    month_file = BASE_DIR / "log" / f"{now.strftime('%Y-%m')}.md"
    month_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%Y-%m-%d %H:%M")
    accion = args.accion.strip().strip("[]")
    desc = args.descripcion.strip()
    proyecto_part = f" — ({args.proyecto.strip()})" if args.proyecto else ""

    line = f"{timestamp} — [{accion}] — {desc}{proyecto_part}\n"

    with open(month_file, "a", encoding="utf-8") as f:
        f.write(line)

    print(f"✓ Registrado en log/{month_file.name}: {line.strip()}")


def cmd_search(args):
    """Búsqueda rápida por palabras clave en los archivos markdown del cerebro."""
    query = args.query.lower()
    layers_to_search = [args.layer] if args.layer else ["verdad", "wiki", "proyectos", "raw"]
    results = []

    for layer in layers_to_search:
        p = BASE_DIR / layer
        if not p.exists():
            continue
        for file_path in p.rglob("*.md"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            rel_path = file_path.relative_to(BASE_DIR)
            matches = []
            for idx, line in enumerate(content.splitlines(), start=1):
                if query in line.lower():
                    matches.append((idx, line.strip()))
                    if len(matches) >= 3:
                        break

            if matches:
                results.append((rel_path, matches))

    print(f"=== BÚSQUEDA: '{args.query}' ({len(results)} archivos encontrados) ===")
    for rel_path, matches in results[:10]:
        print(f"\n📄 {rel_path}:")
        for idx, line in matches:
            snippet = line[:100] + "..." if len(line) > 100 else line
            print(f"  L{idx}: {snippet}")


def cmd_check(args):
    """Verifica la salud e higiene del cerebro agéntico."""
    issues = []
    
    # 1. Inbox check
    inbox_files = [f for f in (BASE_DIR / "inbox").iterdir() if f.is_file() and f.name != ".gitkeep"]
    if inbox_files:
        issues.append(f"Inbox contiene {len(inbox_files)} archivo(s) sin clasificar.")

    # 2. Frontmatter check en wiki y verdad
    for layer in ["wiki", "verdad"]:
        p = BASE_DIR / layer
        if p.exists():
            for f in p.glob("*.md"):
                meta = parse_frontmatter(f)
                if not meta["descripcion"]:
                    issues.append(f"Nota sin descripción en frontmatter: {f.relative_to(BASE_DIR)}")

    # 3. Proyectos check
    proy_dir = BASE_DIR / "proyectos"
    if proy_dir.exists():
        for d in proy_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                if not (d / "estado.md").exists():
                    issues.append(f"Proyecto sin estado.md: {d.name}")

    if issues:
        print(f"⚠️ Se encontraron {len(issues)} observación(es):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Salud del cerebro: Todo en orden, sin anomalías.")


def main():
    parser = argparse.ArgumentParser(description="Gestor de eficiencia para Cerebro Agéntico")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Diagnóstico rápido de capas y proyectos")

    # index
    subparsers.add_parser("index", help="Regenerar index.md (Mapa de Contenidos)")

    # log
    log_parser = subparsers.add_parser("log", help="Registrar acción en la bitácora")
    log_parser.add_argument("accion", help="Tipo de acción (ej. inicialización, creación, síntesis)")
    log_parser.add_argument("descripcion", help="Descripción breve de la acción")
    log_parser.add_argument("--proyecto", "-p", help="Proyecto relacionado (opcional)", default=None)

    # search
    search_parser = subparsers.add_parser("search", help="Buscar en el contenido del cerebro")
    search_parser.add_argument("query", help="Término a buscar")
    search_parser.add_argument("--layer", "-l", help="Capa específica a buscar", choices=LAYERS, default=None)

    # check
    subparsers.add_parser("check", help="Auditar salud e integridad del cerebro")

    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    elif args.command == "index":
        cmd_index(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "check":
        cmd_check(args)


if __name__ == "__main__":
    main()
