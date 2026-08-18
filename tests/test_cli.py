from __future__ import annotations


def test_demo_seed_and_eda_commands(app, tmp_path):
    runner = app.test_cli_runner()
    fixture_dir = tmp_path / "fixture"
    first = runner.invoke(args=["demo", "seed", "--directory", str(fixture_dir)])
    assert first.exit_code == 0, first.output
    second = runner.invoke(args=["demo", "seed", "--directory", str(fixture_dir)])
    assert second.exit_code == 0, second.output
    assert '"samples_inserted": 0' in second.output

    report_dir = tmp_path / "reports"
    eda = runner.invoke(args=["analysis", "eda", "--output", str(report_dir)])
    assert eda.exit_code == 0, eda.output
    assert (report_dir / "eda_summary.json").exists()
    assert (report_dir / "eda.html").exists()

