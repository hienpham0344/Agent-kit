---
name: smart-contract-security-evm
description: "Use when auditing, threat-modeling, or hardening EVM smart contracts, escrow state machines, EIP-712 signatures, or backend blockchain receipt verification."
---

# EVM Smart Contract & Verification Security

## Overview
Apply defense-in-depth across on-chain Solidity contracts and the off-chain backend boundary so neither contract exploits nor spoofed frontend transaction claims can move funds or corrupt state.

## When to Use
- Auditing or reviewing Solidity escrow, payment, staking, or role-based contracts.
- Implementing or reviewing backend transaction/receipt verification against Avalanche/EVM RPCs.
- Designing EIP-712 typed signatures, relayer/AI release flows, or dispute resolution contracts.

## On-Chain Security Checklist
1. **Reentrancy & External Call Safety**:
   - Follow Checks-Effects-Interactions strictly; mutate storage before external calls (`IERC20.safeTransfer`, guard hooks, native `.call`).
   - Add `nonReentrant` to all fund-moving and cross-contract entry points.
2. **Access Control & Least Privilege**:
   - Separate admin, arbiter, and relayer roles (`DEFAULT_ADMIN_ROLE`, `ARBITER_ROLE`, `RELEASE_ROLE`).
   - Never allow an off-chain AI service or relayer to bypass on-chain invariants (`IIntegrityGuard` veto hook + valid escrow state check).
3. **Token & Arithmetic Edge Cases**:
   - Use `SafeERC20` for non-standard ERC-20 tokens (missing bool return).
   - Guard against fee-on-transfer discrepancies (measure `balanceAfter - balanceBefore` when supporting arbitrary tokens) and round protocol fees conservatively in the vault's favor.
4. **Signature & Replay Hardening (EIP-712)**:
   - Include `block.chainid`, `address(this)`, monotonic per-signer `nonce`, and `deadline` in signed payloads. Never accept raw hashes across chains or contracts.

## Off-Chain Verification Trust Boundary (Fail Closed)
**Rule: Never trust client-submitted transaction status, block numbers, or decoded amounts.**

When the backend verifies an on-chain action by `txHash`:
1. **Fetch Receipt Directly from Trusted RPC**: Call `eth_getTransactionReceipt` on the configured network RPC (`chainId` must match expected network, e.g., `43113` or `43114`).
2. **Require Success & Confirmations**: Verify `receipt.status == 0x1` and `(latestBlock - receipt.blockNumber + 1) >= requiredConfirmations`.
3. **Verify Contract & Event Authenticity**:
   - Confirm `log.address` equals the deployed contract address configured in backend environment variables.
   - Match exact `topic0` (`keccak256("EscrowFunded(bytes32,address,uint256)")`) and decode indexed/non-indexed fields to verify `dealId`, `buyer`, `token`, and `amount >= expectedAmount`.
4. **Idempotency & Replay Protection**:
   - Persist a unique constraint on `(network, tx_hash)` or `(network, tx_hash, log_index)` so the same on-chain deposit cannot confirm two deals.
5. **Failure Mode**: If the RPC is unreachable or verification is inconclusive, fail closed (reject or keep `PENDING`) — never mark `CONFIRMED`.

## Common Pitfalls
- Checking only `txReceipt.status == 1` without checking `log.address` and event arguments (attacker submits a valid tx to a dummy contract!).
- Allowing a relayer role to call `refund` or change `seller`/`buyer` after funding.
- Skipping fuzz/invariant checks on escrow conservation (`contractBalance >= sum(activeEscrows)`).
