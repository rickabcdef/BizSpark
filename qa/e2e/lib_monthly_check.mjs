/**
 * lib_monthly_check.mjs — T-31 系列（PM 2026-11-16 新增，H-02 框架接入）
 *
 * 验证 F09 月度库检查全链路（bridge 层编排 + F 的 apply_delta）：
 *   T-31-1 强制检查：2026-12 托管包静默并入（版本 2026.11 → 2026.12，时间线留痕）
 *   T-31-2 门槛拦截：盖戳后 30 天内/非 1 号不重查——即使托管上已有 2027-01 也不动
 *   T-31-3 越门槛合并：强制越过门槛后 2027-01 包并入
 *   T-31-4 拉取失败静默：托管源不可达 → skipped、库保持原样、零报错
 *
 * 托管源用本地目录模拟（生产是 BIZSPARK_HOST_URL 静态托管，行为同构）。
 * 用法：node e2e/lib_monthly_check.mjs   （退出码 0=全过）
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { startBridge } from "./bridge_server.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");
const HOSTING = path.join(REPO, "hosting");

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "bizspark-libcheck-"));

let pass = 0;
let fail = 0;
function check(name, cond, detail = "") {
  const ok = !!cond;
  if (ok) pass += 1;
  else fail += 1;
  console.log(`  [${ok ? "PASS" : "FAIL"}] ${name}${detail ? "  · " + detail : ""}`);
}

/** 伪造一期"下一月"托管包（空操作 delta：只推进版本，不动数据） */
function fakeHosting(latest, release) {
  const dir = tmp();
  fs.writeFileSync(
    path.join(dir, "manifest.json"),
    JSON.stringify({ latest, files: [`delta_${latest}.json`], size_kb: 1,
                     min_client: "1.0.0", published_at: release }, null, 1),
  );
  fs.writeFileSync(
    path.join(dir, `delta_${latest}.json`),
    JSON.stringify({ target_baseline: "v1", release: `${release}`, add: [], revise: [], retire: [] }, null, 1),
  );
  return dir;
}

async function stateOf(bridge) {
  const st = await bridge.sidecar.call("get_state");
  return st?.data || {};
}

// ---- T-31-1 / T-31-2 / T-31-3：同一 appData 串行演进（先关再开，避免双写） ----
{
  const appData = tmp();

  // T-31-1 强制检查：真托管目录（hosting/，latest=2026-12）
  const b1 = await startBridge({ appData, locale: "zh-CN", manifestUrl: HOSTING, forceLibCheck: true });
  const r1 = await b1.libCheckPromise;
  const s1 = await stateOf(b1);
  await b1.close();
  const tl = Array.isArray(s1.timeline) ? s1.timeline[s1.timeline.length - 1] : null;
  check("T-31-1 强制月度检查并入 2026-12 包",
    r1?.applied?.length === 1 && r1.applied[0].applied === true && s1.library_version === "2026.12",
    `applied=${JSON.stringify(r1?.applied)} version=${s1.library_version} ideas=${s1.library_ideas}`);
  check("T-31-1b 时间线留痕", tl?.release === "2026-12-01",
    `timeline_last=${JSON.stringify(tl)}`);

  // T-31-2 门槛拦截：不强制（刚盖过戳、非 1 号、<30 天）→ 有 2027-01 也不动
  const host27 = fakeHosting("2027-01", "2027-01-01");
  const b2 = await startBridge({ appData, locale: "zh-CN", manifestUrl: host27 });
  const r2 = await b2.libCheckPromise;
  const s2 = await stateOf(b2);
  await b2.close();
  check("T-31-2 门槛拦截（30 天内不重查）",
    r2?.skipped === "not-due" && s2.library_version === "2026.12",
    `skipped=${r2?.skipped} version=${s2.library_version}`);

  // T-31-3 强制越过门槛 → 2027-01 并入
  const b3 = await startBridge({ appData, locale: "zh-CN", manifestUrl: host27, forceLibCheck: true });
  const r3 = await b3.libCheckPromise;
  const s3 = await stateOf(b3);
  await b3.close();
  check("T-31-3 强制越过门槛合并 2027-01",
    r3?.applied?.length === 1 && s3.library_version === "2027.01",
    `skipped=${r3?.skipped} applied=${JSON.stringify(r3?.applied)} version=${s3.library_version}`);
}

// ---- T-31-4 拉取失败静默 ----
{
  const appData = tmp();
  const b = await startBridge({
    appData, locale: "zh-CN",
    manifestUrl: path.join(tmp(), "no-such-hosting"),
    forceLibCheck: true,
  });
  const r = await b.libCheckPromise;
  const s = await stateOf(b);
  await b.close();
  check("T-31-4 拉取失败静默且库不动",
    r?.skipped === "fetch-failed" && s.library_version === "2026.11",
    `skipped=${r?.skipped} version=${s.library_version}`);
}

console.log(fail ? `T-31 FAIL ${fail}/${pass + fail}` : `T-31 PASS ${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
