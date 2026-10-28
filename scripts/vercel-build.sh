#!/usr/bin/env bash
set -euo pipefail
if ! command -v rustup >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
fi
if [ -f "$HOME/.cargo/env" ]; then . "$HOME/.cargo/env"; fi
export PATH="$HOME/.cargo/bin:$PATH"
rustup default stable >/dev/null 2>&1 || rustup toolchain install stable --profile minimal
rustup target add wasm32-unknown-unknown
rustup toolchain install nightly --profile minimal --component rust-src
rustup target add wasm32-unknown-unknown --toolchain nightly
rustup show active-toolchain
CI=false npx turbo build --filter=@opendaw/app-studio --env-mode=loose --force --output-logs=errors-only
