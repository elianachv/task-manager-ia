"""Recolección de resultados y generación de informes de pruebas."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

CP_PATTERN = re.compile(r"CP-(\d+)", re.IGNORECASE)
TEST_CP_PATTERN = re.compile(r"test_cp(\d+)_", re.IGNORECASE)

CATEGORY_LABELS = {
    "unit": "Unitarias",
    "integration": "Integración API",
    "e2e": "E2E / UI",
    "other": "Otras",
}


@dataclass
class TestResult:
    nodeid: str
    name: str
    case_id: str
    category: str
    description: str
    outcome: str
    duration_ms: float
    message: str = ""

    @property
    def status_icon(self) -> str:
        return {"passed": "✅", "failed": "❌", "skipped": "⏭️", "error": "💥"}.get(
            self.outcome, "❓"
        )


@dataclass
class TestReportCollector:
    started_at: datetime | None = None
    finished_at: datetime | None = None
    results: list[TestResult] = field(default_factory=list)
    _active: dict[str, datetime] = field(default_factory=dict)
    _descriptions: dict[str, str] = field(default_factory=dict)

    def reset(self) -> None:
        self.started_at = datetime.now()
        self.finished_at = None
        self.results = []
        self._active = {}
        self._descriptions = {}

    def on_session_start(self) -> None:
        self.reset()
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def on_test_start(self, item: pytest.Item) -> None:
        self._active[item.nodeid] = datetime.now()
        case_id = _extract_case_id(item)
        category = _extract_category(item)
        description = _extract_description(item)
        self._descriptions[item.nodeid] = description
        print(
            f"\n▶ Iniciando {case_id} [{CATEGORY_LABELS.get(category, category)}] "
            f"{item.name}\n  {description}",
            flush=True,
        )

    def on_test_finish(self, report: pytest.TestReport) -> None:
        if report.when != "call":
            return

        started = self._active.pop(report.nodeid, datetime.now())
        finished = datetime.now()
        duration_ms = (finished - started).total_seconds() * 1000

        item = report.nodeid
        case_id = _extract_case_id_from_nodeid(item)
        category = _extract_category_from_nodeid(item)
        description = self._descriptions.get(
            report.nodeid, _extract_description_from_nodeid(report)
        )

        message = ""
        if report.failed:
            message = str(report.longreprtext or report.longrepr or "")

        result = TestResult(
            nodeid=item,
            name=item.split("::")[-1],
            case_id=case_id,
            category=category,
            description=description,
            outcome=report.outcome,
            duration_ms=duration_ms,
            message=message,
        )
        self.results.append(result)

        status = result.status_icon
        print(
            f"{status} Finalizado {case_id} en {duration_ms:.0f} ms — {report.outcome.upper()}",
            flush=True,
        )
        if message and report.failed:
            print(textwrap.indent(message[:500], "   "), flush=True)

    def finalize(self, exitstatus: int) -> Path:
        self.finished_at = datetime.now()
        timestamp = self.finished_at.strftime("%Y%m%d_%H%M%S")
        text_path = REPORTS_DIR / f"informe_{timestamp}.txt"
        html_path = REPORTS_DIR / f"informe_{timestamp}.html"
        latest_text = REPORTS_DIR / "ultimo_informe.txt"
        latest_html = REPORTS_DIR / "ultimo_informe.html"

        text_content = self._build_text_report(exitstatus)
        html_content = self._build_html_report(exitstatus)

        text_path.write_text(text_content, encoding="utf-8")
        html_path.write_text(html_content, encoding="utf-8")
        latest_text.write_text(text_content, encoding="utf-8")
        latest_html.write_text(html_content, encoding="utf-8")

        print("\n" + "=" * 72, flush=True)
        print(text_content, flush=True)
        print("=" * 72, flush=True)
        print(f"\n📄 Informe guardado en:\n   - {text_path}\n   - {html_path}", flush=True)
        print(f"📄 Copia rápida:\n   - {latest_text}\n   - {latest_html}", flush=True)

        return text_path

    def _build_text_report(self, exitstatus: int) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.outcome == "passed")
        failed = sum(1 for r in self.results if r.outcome == "failed")
        skipped = sum(1 for r in self.results if r.outcome == "skipped")
        errors = sum(1 for r in self.results if r.outcome == "error")
        total_ms = sum(r.duration_ms for r in self.results)

        started = self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else "-"
        finished = self.finished_at.strftime("%Y-%m-%d %H:%M:%S") if self.finished_at else "-"
        session_seconds = (
            (self.finished_at - self.started_at).total_seconds()
            if self.started_at and self.finished_at
            else 0
        )

        lines = [
            "INFORME FINAL DE PRUEBAS — GESTOR DE TAREAS",
            "",
            f"Inicio:     {started}",
            f"Fin:        {finished}",
            f"Duración:   {session_seconds:.2f} s",
            f"Estado:     {'EXITOSO' if exitstatus == 0 else 'CON FALLOS'} (código {exitstatus})",
            "",
            "RESUMEN",
            f"  Total:    {total}",
            f"  Pasaron:  {passed}",
            f"  Fallaron: {failed}",
            f"  Omitidos: {skipped}",
            f"  Errores:  {errors}",
            f"  Tiempo tests: {total_ms:.0f} ms",
            "",
        ]

        for category_key, label in CATEGORY_LABELS.items():
            if category_key == "other":
                continue
            cat_results = [r for r in self.results if r.category == category_key]
            if not cat_results:
                continue
            cat_passed = sum(1 for r in cat_results if r.outcome == "passed")
            lines.append(f"{label}: {cat_passed}/{len(cat_results)} exitosas")
            lines.append("-" * 72)
            for result in cat_results:
                lines.append(
                    f"  {result.status_icon} {result.case_id:<8} "
                    f"{result.duration_ms:>7.0f} ms  {result.description}"
                )
                if result.message and result.outcome == "failed":
                    snippet = result.message.strip().splitlines()[0][:120]
                    lines.append(f"      ↳ {snippet}")
            lines.append("")

        if failed or errors:
            lines.append("DETALLE DE FALLOS")
            lines.append("-" * 72)
            for result in self.results:
                if result.outcome in {"failed", "error"}:
                    lines.append(f"{result.case_id} — {result.name}")
                    lines.append(textwrap.indent(result.message[:2000], "  "))
                    lines.append("")

        return "\n".join(lines)

    def _build_html_report(self, exitstatus: int) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.outcome == "passed")
        failed = sum(1 for r in self.results if r.outcome == "failed")
        skipped = sum(1 for r in self.results if r.outcome == "skipped")

        rows = "\n".join(
            f"<tr class='{r.outcome}'><td>{r.status_icon}</td><td>{r.case_id}</td>"
            f"<td>{CATEGORY_LABELS.get(r.category, r.category)}</td>"
            f"<td>{r.description}</td><td>{r.outcome}</td>"
            f"<td>{r.duration_ms:.0f} ms</td></tr>"
            for r in self.results
        )

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Informe de pruebas — Gestor de Tareas</title>
  <style>
    body {{ font-family:Segoe UI,sans-serif; margin:2rem; background:#f5f7f8; color:#1f2937; }}
    h1 {{ color:#0f766e; }}
    .summary {{ background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:1rem; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; margin-top:1rem; }}
    th, td {{ border:1px solid #e5e7eb; padding:0.6rem; text-align:left; }}
    th {{ background:#e8fbf8; }}
    tr.failed {{ background:#fef2f2; }}
    tr.passed {{ background:#ecfdf5; }}
    tr.skipped {{ background:#fff7ed; }}
  </style>
</head>
<body>
  <h1>Informe de pruebas — Gestor de Tareas</h1>
  <div class="summary">
    <p><strong>Estado:</strong> {'EXITOSO' if exitstatus == 0 else 'CON FALLOS'}</p>
    <p><strong>Total:</strong> {total} |
       <strong>Pasaron:</strong> {passed} |
       <strong>Fallaron:</strong> {failed} |
       <strong>Omitidos:</strong> {skipped}</p>
  </div>
  <table>
    <thead><tr><th></th><th>Caso</th><th>Categoría</th><th>Descripción</th><th>Resultado</th><th>Duración</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""


report_collector = TestReportCollector()


def _extract_case_id(item: pytest.Item) -> str:
    return _extract_case_id_from_nodeid(item.nodeid)


def _extract_case_id_from_nodeid(nodeid: str) -> str:
    match = TEST_CP_PATTERN.search(nodeid)
    if match:
        return f"CP-{match.group(1).zfill(2)}"
    doc_match = CP_PATTERN.search(nodeid)
    if doc_match:
        return f"CP-{doc_match.group(1).zfill(2)}"
    return "N/A"


def _extract_category(item: pytest.Item) -> str:
    return _extract_category_from_nodeid(item.nodeid)


def _extract_category_from_nodeid(nodeid: str) -> str:
    normalized = nodeid.replace("\\", "/")
    if normalized.startswith("unit/") or "/unit/" in normalized:
        return "unit"
    if normalized.startswith("integration/") or "/integration/" in normalized:
        return "integration"
    if normalized.startswith("e2e/") or "/e2e/" in normalized:
        return "e2e"
    return "other"


def _extract_description(item: pytest.Item) -> str:
    doc = getattr(item.obj, "__doc__", None) or item.name
    return doc.strip().splitlines()[0] if doc else item.name


def _extract_description_from_nodeid(report: pytest.TestReport) -> str:
    if report.user_properties:
        for key, value in report.user_properties:
            if key == "description":
                return str(value)
    name = report.nodeid.split("::")[-1]
    return name.replace("_", " ")
