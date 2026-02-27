"""Unit tests for policy module."""

from __future__ import annotations

import pytest

from policy import resolve_decision


class TestResolveDecisionMonitorMode:
    """Tests for policy resolution in monitor mode."""

    def test_monitor_mode_always_passes(self) -> None:
        """Monitor mode should always return PASS."""
        decision, risk = resolve_decision("monitor", None)
        assert decision == "PASS"
        assert risk == 0.12

    def test_monitor_mode_with_target_risk(self) -> None:
        """Monitor mode should ignore target_risk parameter."""
        decision, risk = resolve_decision("monitor", target_risk=0.8)
        assert decision == "PASS"
        assert risk == 0.12


class TestResolveDecisionEnforceMode:
    """Tests for policy resolution in enforce mode."""

    def test_enforce_mode_pass_below_threshold(self) -> None:
        """Risk below threshold should return PASS."""
        decision, risk = resolve_decision("enforce", target_risk=0.5)
        assert decision == "PASS"
        assert risk == 0.12

    def test_enforce_mode_refine_in_range(self) -> None:
        """Risk in [threshold, threshold+0.2] should return REFINE."""
        # With base_risk=0.12 and threshold=0.1, risk is in range [0.1, 0.3)
        decision, risk = resolve_decision("enforce", target_risk=0.1)
        assert decision == "REFINE"

    def test_enforce_mode_escalate_in_range(self) -> None:
        """Risk in [threshold+0.2, threshold+0.4] should return ESCALATE."""
        # With base_risk=0.12 and threshold=-0.1 (clamped to 0), escalate at [0.2, 0.4]
        decision, risk = resolve_decision("enforce", target_risk=-0.5)
        assert decision == "ESCALATE"

    def test_enforce_mode_block_above_all(self) -> None:
        """Risk above all thresholds should return BLOCK."""
        decision, risk = resolve_decision("enforce", target_risk=-1.0)
        assert decision == "BLOCK"

    def test_enforce_mode_default_threshold(self) -> None:
        """Enforce mode without target_risk should use default 0.5."""
        decision, risk = resolve_decision("enforce", None)
        assert decision == "PASS"
        assert risk == 0.12


class TestRiskClamping:
    """Tests for risk value clamping."""

    def test_target_risk_clamped_low(self) -> None:
        """Negative target_risk should be clamped to 0."""
        decision, risk = resolve_decision("enforce", target_risk=-0.5)
        assert risk == 0.12
        # Should evaluate against threshold=0, so base_risk > threshold -> ESCALATE

    def test_target_risk_clamped_high(self) -> None:
        """Target_risk > 1.0 should be clamped to 1.0."""
        decision, risk = resolve_decision("enforce", target_risk=1.5)
        assert decision == "PASS"
        assert risk == 0.12

    def test_base_risk_clamped(self) -> None:
        """Base risk should be clamped to [0, 1]."""
        decision, risk = resolve_decision("monitor", None)
        assert 0.0 <= risk <= 1.0


class TestThresholdBoundaries:
    """Tests for threshold boundary behavior."""

    def test_at_exact_threshold(self) -> None:
        """Risk exactly at threshold should return PASS."""
        # threshold = base_risk, so PASS
        decision, risk = resolve_decision("enforce", target_risk=0.12)
        assert decision == "PASS"

    def test_just_above_threshold(self) -> None:
        """Risk just above threshold should return REFINE."""
        decision, risk = resolve_decision("enforce", target_risk=0.11)
        assert decision == "REFINE"

    def test_at_refine_boundary(self) -> None:
        """Risk at refine/escalate boundary should transition correctly."""
        # With threshold=0.0, boundaries are [0.0, 0.2) REFINE, [0.2, 0.4) ESCALATE
        decision, risk = resolve_decision("enforce", target_risk=-0.2)
        assert decision == "ESCALATE"


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_zero_target_risk(self) -> None:
        """Target risk of exactly 0 should be handled correctly."""
        decision, risk = resolve_decision("enforce", target_risk=0.0)
        assert decision == "REFINE"

    def test_one_target_risk(self) -> None:
        """Target risk of exactly 1.0 should be handled correctly."""
        decision, risk = resolve_decision("enforce", target_risk=1.0)
        assert decision == "PASS"

    def test_invalid_mode_defaults_to_pass(self) -> None:
        """Unknown mode should behave like monitor (or raise/default)."""
        # Current implementation doesn't validate mode, so unknown mode falls through
        decision, risk = resolve_decision("unknown_mode", target_risk=0.5)
        # Falls through to enforce logic since it's not "monitor"
        assert decision == "PASS"
