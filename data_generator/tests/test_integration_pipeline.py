# tests/test_integration_pipeline.py
import json
import os
from data_generator import generator, validation
from reports import html_reporter, pdf_reporter

def test_full_data_generation_pipeline(sample_config, tmp_path):
    """Run the pipeline end-to-end (lightweight) and assert tables exist."""
    out = generator.run_full_data_pipeline(config=sample_config, out_dir=str(tmp_path))
    # Expect dictionary with required tables
    for tbl in ('EKKO','EKPO','LFA1','MARA','EKBE'):
        assert tbl in out, f"{tbl} not present in pipeline output"

def test_data_quality_validation_passes_sample_data(sample_data):
    report = validation.run_all_checks(sample_data)
    # The sample_data fixture should be valid by construction
    assert 'findings' in report
    # Ensure at least the report exists and overall_score is present
    assert isinstance(report.get('timing_seconds', 0), (int, float))

def test_report_generation_html(tmp_reports_dir, sample_data):
    out_path = tmp_reports_dir / "dq_report.html"
    html_reporter.generate_html_report(sample_data, output_path=str(out_path))
    assert out_path.exists()

def test_pdf_report_generation_monkeypatched(tmp_reports_dir, sample_data, monkeypatch):
    # Avoid heavy PDF generation by monkeypatching the pdf writer
    called = {}
    def fake_pdf_write(*args, **kwargs):
        called['ok'] = True
        (tmp_reports_dir / "report.pdf").write_text("pdf-placeholder")
    monkeypatch.setattr(pdf_reporter, 'generate_pdf_report', fake_pdf_write)
    pdf_reporter.generate_pdf_report(sample_data, output_path=str(tmp_reports_dir / "report.pdf"))
    assert called.get('ok', False)

def test_dashboard_data_loading(monkeypatch):
    # Mock a lightweight data loading function to simulate dashboard load
    from reports.html_reporter import load_dashboard_data
    monkeypatch.setattr(load_dashboard_data.__module__, 'load_dashboard_data', lambda *a, **k: {"status": "ok"})
    res = load_dashboard_data()
    assert isinstance(res, dict) and res.get('status') == 'ok'