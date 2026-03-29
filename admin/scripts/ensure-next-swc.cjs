/**
 * Next optional @next/swc-* binaries match the OS that ran `npm install`.
 * Installing with Windows npm into a WSL filesystem often leaves only
 * @next/swc-win32-x64-msvc, while `next dev` under Linux needs @next/swc-linux-*.
 * This script installs the Linux package when running under Linux and it's missing.
 */
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const root = path.join(__dirname, "..");
const nextJson = path.join(root, "node_modules", "next", "package.json");

function main() {
  if (!fs.existsSync(nextJson)) {
    return;
  }

  const { version } = JSON.parse(fs.readFileSync(nextJson, "utf8"));
  const suffix =
    process.platform === "linux"
      ? { x64: "linux-x64-gnu", arm64: "linux-arm64-gnu" }[process.arch]
      : null;

  if (!suffix) {
    return;
  }

  const pkg = `@next/swc-${suffix}`;
  const marker = path.join(root, "node_modules", "@next", `swc-${suffix}`, "package.json");

  if (fs.existsSync(marker)) {
    return;
  }

  console.warn(`[admin] Installing missing ${pkg}@${version} for Next.js (native SWC).`);
  execSync(`npm install ${pkg}@${version} --no-audit --no-fund --ignore-scripts`, {
    cwd: root,
    stdio: "inherit",
  });
}

main();
