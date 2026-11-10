---
name: avalanche-solidity-hardhat
description: "Use when writing, testing, compiling, or deploying Solidity smart contracts on Avalanche C-Chain or Fuji testnet with Hardhat, Foundry, OpenZeppelin, and viem."
---

# Avalanche Solidity, Hardhat & Foundry Engineering

## Overview
Build deterministic, upgrade-safe, gas-aware EVM smart contracts for Avalanche C-Chain (`43114`) and Fuji testnet (`43113`) using Solidity `0.8.28+`, OpenZeppelin `5.x`, Hardhat/viem, and Foundry (`forge`/`anvil`).

## When to Use
- Creating or modifying Solidity contracts, interfaces, or guard hooks for Avalanche.
- Writing Hardhat 3 + viem or Foundry (`forge test`, fuzz/invariant) suites and deployment scripts.
- Configuring Avalanche Fuji (`43113`) or Mainnet (`43114`) RPCs, ABI exports, and explorer verification.

## Avalanche Network Essentials
| Network | Chain ID | Default RPC | Native Gas | Explorer |
| :--- | :--- | :--- | :--- | :--- |
| Avalanche C-Chain | `43114` | `https://api.avax.network/ext/bc/C/rpc` | AVAX | Snowtrace / Routescan |
| Avalanche Fuji Testnet | `43113` | `https://api.avax-test.network/ext/bc/C/rpc` | AVAX (faucet) | `testnet.snowtrace.io` |

- **Finality**: Snowman consensus provides fast sub-2s deterministic finality on C-Chain; still enforce configurable block confirmations in off-chain indexers.
- **Secrets**: Never hardcode `DEPLOYER_PRIVATE_KEY` in `hardhat.config.ts`. Read from `process.env.DEPLOYER_PRIVATE_KEY` only when deploying, and default to `[]` for compile/test runs.

## Smart Contract Standards (Solidity 0.8.x + OpenZeppelin 5.x)
1. **Explicit State Machines & Checks-Effects-Interactions (CEI)**:
   - Update `status` and accounting state *before* external token transfers or hook calls.
   - Apply `ReentrancyGuard` (`nonReentrant`) on every function that transfers native AVAX or ERC-20 tokens.
2. **Safe Token Handling**:
   - Always use `SafeERC20` (`safeTransfer`, `safeTransferFrom`) — never bare `transfer`/`transferFrom`.
   - Never assume 18 decimals; USDC/USDT on Avalanche commonly use `6` decimals.
3. **Custom Errors & Strict Validation**:
   - Prefer custom errors (`error InvalidState(Status current, Status expected);`) over long `require(..., "string")` messages to reduce bytecode and gas.
   - Validate zero addresses, `amount > 0`, and role separation (`seller != buyer`).
4. **Access Control & Guard Hooks**:
   - Use OpenZeppelin `AccessControl` with distinct operational roles (`ARBITER_ROLE`, `RELEASE_ROLE`) instead of monolithic `onlyOwner`.
   - When off-chain backends or AI workflows trigger state changes, enforce an on-chain `IIntegrityGuard` check before releasing funds.
5. **Indexed Events for Off-Chain Indexing**:
   - Emit events on every state transition with `indexed` identifiers (`dealId`, `buyer`, `seller`) so backend verifiers and subgraphs can filter logs deterministically.

## Hardhat 3 + Viem / Foundry Workflow
```bash
# Hardhat 3 + viem
npx hardhat compile && npx hardhat test
npx hardhat ignition deploy ignition/modules/Deploy.ts --network fuji

# Foundry (forge / anvil / cast)
forge build && forge test --fuzz-runs 256
forge script script/Deploy.s.sol --rpc-url fuji --broadcast
```
- **Deterministic Tests**: Deploy fresh contract instances per test (`viem.deployContract` or Foundry `setUp()`), assert custom error reverts (`revertWithCustomError` / `vm.expectRevert`), and add stateful invariant tests for escrow conservation.
- **ABI Sync**: After contract edits, re-compile (`forge build` / `abi:export`) and sync ABIs to backend (`web3j`/JSON) and frontend (`viem`) consumers.

## Common Mistakes
- Assuming `tx.origin` for auth or forgetting `nonReentrant` around `safeTransferFrom` / external guard calls.
- Deploying to Fuji without setting gas/accounts conditionally, breaking CI compilation when `DEPLOYER_PRIVATE_KEY` is unset.
- Emitting state-changing events without `indexed` deal/order IDs or storing token amounts as `uint64` instead of `uint256`.
