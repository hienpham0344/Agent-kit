---
name: wagmi-viem-web3-frontend
description: "Use when building or debugging Avalanche or EVM frontend wallet flows, typed ABI contract reads/writes, token approvals, or transaction receipts with wagmi, viem, and Next.js."
---

# Wagmi, Viem & Avalanche Web3 Frontend

## Overview
Build type-safe, hydration-clean, resilient Web3 user interfaces for Avalanche and EVM chains using `wagmi`, `viem`, Next.js App Router, and TanStack Query.

## When to Use
- Configuring `wagmi` chains/transports (`avalancheFuji`, `avalanche`) in Next.js (`ssr: true`).
- Implementing wallet connect, network switching, ERC-20 `approve` + contract `writeContract` flows, or receipt confirmation tracking.
- Formatting/parsing token amounts with `bigint` or decoding custom Solidity errors in UI feedback.

## Core Patterns & Rules
1. **Typed ABIs (`as const`)**:
   - Export ABIs as `const` TypeScript tuples or typed JSON assertions so `useReadContract` and `useWriteContract` infer function names, argument tuples, and return types at compile time.
2. **Next.js App Router SSR Safety**:
   - Keep `ssr: true` in `createConfig` and gate wallet-specific rendering (`address`, `isConnected`, `chainId`) behind a client-mounted check (`useEffect` mounted flag or `useConnection` status guard) to prevent React hydration mismatches.
3. **Exact `bigint` Token Math (Never JS `number`)**:
   ```typescript
   import { formatUnits, parseUnits } from "viem";

   const rawAmount = parseUnits(userInput, tokenDecimals); // e.g. 6 for USDC, 18 for AVAX
   const display = formatUnits(rawAmount, tokenDecimals);
   ```
   - Never multiply by `1e18` in JavaScript floating-point numbers.
4. **Two-Step ERC-20 Approve & Write Flow**:
   - Read current `allowance(owner, spender)` first; skip `approve` if `allowance >= amount`.
   - Run `simulateContract` before `writeContract` to surface Solidity custom errors *before* opening the wallet popup.
   - Track mining with `useWaitForTransactionReceipt({ hash })`, then invalidate TanStack Query keys and notify the backend with `txHash` (let the backend verify on-chain independently).
5. **Wrong-Network & Error UX**:
   - Compare `chainId !== targetChain.id` and provide a one-click `useSwitchChain` action before enabling write buttons.
   - Distinguish `UserRejectedRequestError` (user cancelled cleanly) from `ContractFunctionRevertedError` (show decoded custom error name/reason).

## Common Mistakes
- Reading `useAccount().address` directly during SSR render, causing hydration errors in Next.js.
- Calling `writeContract` for `fundEscrow` in parallel with `approve` without awaiting `approve` receipt confirmation first.
- Marking a deal as funded in frontend state before both on-chain receipt confirmation and backend verification succeed.
