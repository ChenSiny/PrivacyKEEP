"""Proof-of-concept test for the educational Schnorr-like ring signature implementation.
Run directly: python backend/tests/demo_ring_test.py

Demonstrates:
1. Successful ring signature generation & verification
2. Failure if any s component is tampered
3. Failure if c0 is tampered
"""
import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Ensure backend package import
sys.path.append(str(ROOT))

from app.services.crypto_service import CryptoService

def hex_shorten(h: str, length: int = 16) -> str:
    return h[:length] + ('...' if len(h) > length else '')

def run_demo():
    # Prepare a mock ring of public keys via keypair generation
    # Use generate_keypair repeatedly; if coincurve missing it raises, test will fail accordingly.
    keypairs = [CryptoService.generate_keypair() for _ in range(3)]
    priv0 = keypairs[0]['private_key']
    ring_pubkeys = [kp['public_key'] for kp in keypairs]

    message = b"ring_demo|5.40|6.20"  # ring_id|distance|pace
    print("Message:", message.decode())
    print("Ring size:", len(ring_pubkeys))

    # Sign
    c0, s_list = CryptoService.ring_sign(message, priv0, ring_pubkeys)
    print("Generated c0:", hex_shorten(c0))
    print("First s scalar:", hex_shorten(s_list[0]))

    # Verify success
    ok = CryptoService.ring_verify(message, ring_pubkeys, c0, s_list)
    print("Verify (original):", ok)

    # Tamper s[1]
    s_tamper = s_list.copy()
    s_tamper[1] = ('0' * 64) if s_tamper[1][0] != '0' else ('f' * 64)
    ok_tamper_s = CryptoService.ring_verify(message, ring_pubkeys, c0, s_tamper)
    print("Verify (tampered s[1]):", ok_tamper_s)

    # Tamper c0
    c0_bad = ('0' * 64) if c0[0] != '0' else ('f' * 64)
    ok_tamper_c0 = CryptoService.ring_verify(message, ring_pubkeys, c0_bad, s_list)
    print("Verify (tampered c0):", ok_tamper_c0)

    # Summary block
    summary = {
        "ring_size": len(ring_pubkeys),
        "c0_prefix": c0[:16],
        "s0_prefix": s_list[0][:16],
        "verify_original": ok,
        "verify_tamper_s": ok_tamper_s,
        "verify_tamper_c0": ok_tamper_c0,
    }
    print("\nJSON Summary:\n" + json.dumps(summary, indent=2))

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print("Test encountered an error:", e)
        sys.exit(1)
