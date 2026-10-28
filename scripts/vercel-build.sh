#!/usr/bin/env bash
set -euo pipefail
if ! command -v rustup >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
fi
. "$HOME/.cargo/env"
rustup target add wasm32-unknown-unknown
rustup toolchain install nightly --profile minimal --component rust-src
rustup target add wasm32-unknown-unknown --toolchain nightly
CI=false npx turbo build --filter=@opendaw/app-studio --output-logs=errors-only
