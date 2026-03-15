"""Tests for CLI functionality."""

import pytest
from click.testing import CliRunner
from reference_toolkit.cli import main


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


class TestCLICommands:
    """Tests for CLI command availability."""

    def test_main_help(self, runner):
        """Test that main help command works."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Reference Toolkit" in result.output
        assert "search" in result.output
        assert "resolve" in result.output
        assert "download" in result.output
        assert "rename" in result.output

    def test_search_help(self, runner):
        """Test search command help."""
        result = runner.invoke(main, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search for papers" in result.output

    def test_resolve_help(self, runner):
        """Test resolve command help."""
        result = runner.invoke(main, ["resolve", "--help"])
        assert result.exit_code == 0
        assert "Resolve references" in result.output

    def test_download_help(self, runner):
        """Test download command help."""
        result = runner.invoke(main, ["download", "--help"])
        assert result.exit_code == 0
        assert "Download open-access PDFs" in result.output

    def test_rename_help(self, runner):
        """Test rename command help."""
        result = runner.invoke(main, ["rename", "--help"])
        assert result.exit_code == 0
        assert "Rename PDF files" in result.output
        assert "--dry-run" in result.output
        assert "--output-dir" in result.output

    def test_pipeline_help(self, runner):
        """Test pipeline command help."""
        result = runner.invoke(main, ["pipeline", "--help"])
        assert result.exit_code == 0
        assert "Full Pipeline" in result.output

    def test_convert_help(self, runner):
        """Test convert command help."""
        result = runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0
        assert "Convert between reference formats" in result.output

    def test_contacts_help(self, runner):
        """Test contacts command help."""
        result = runner.invoke(main, ["contacts", "--help"])
        assert result.exit_code == 0
        assert "Extract author contacts" in result.output


class TestCLIErrors:
    """Tests for CLI error handling."""

    def test_missing_command(self, runner):
        """Test error when no command provided."""
        result = runner.invoke(main, [])
        assert result.exit_code != 0

    def test_invalid_command(self, runner):
        """Test error with invalid command."""
        result = runner.invoke(main, ["invalid_command"])
        assert result.exit_code != 0

    def test_rename_missing_folder(self, runner):
        """Test rename command without folder argument."""
        result = runner.invoke(main, ["rename"])
        assert result.exit_code != 0
        assert "missing" in result.output.lower() or "required" in result.output.lower()
