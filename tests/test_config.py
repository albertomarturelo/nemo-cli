"""Tests for nemo_cli.config."""

from __future__ import annotations

from nemo_cli.config import API_BASE_URL


class TestApiBaseUrl:
    def test_points_to_production_root(self) -> None:
        assert API_BASE_URL == "https://portalclientes.vectorcapital.cl/api"
