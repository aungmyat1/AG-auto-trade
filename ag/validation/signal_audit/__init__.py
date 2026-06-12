"""Signal Audit Framework — Phase A infrastructure.

Tracks the signal generation funnel to identify bottlenecks before adding
more SMC features.  Required output before any further feature work:

  Liquidity sweeps:  X,XXX
  ChoCH events:        XXX
  OB touches:          XXX
  Entries generated:    XX
  Trades executed:      XX

Without this data, every optimization is blind.
"""
from .tracker import SignalFunnelTracker, RejectionReason

__all__ = ["SignalFunnelTracker", "RejectionReason"]
