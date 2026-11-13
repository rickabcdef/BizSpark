/**
 * cmd.ts — B-05（负责人：B，A 审）
 * 唯一 IPC 出口：封装 §2.4 命令表全部 cmd，统一超时与静默失败。
 * 铁律：组件里零 fetch、零 invoke，一律经本文件。
 *
 * 链路：cmd.ts → invoke("handle_core_cmd") → A 的 bridge.rs → sidecar
 * 协议：{ req_id, cmd, payload } → { req_id, ok, data? | error:{code,message?} }
 * 超时：§2.4 请求级 800ms（诊断类 C-08 允许放宽到 30s，见 TIMEOUT_DIAGNOSE）
 * 失败：静默——返回 null，由视图层走空态/降级，绝不弹错（§2.4 边界）
 */

const DEFAULT_TIMEOUT = 800;
/** diagnose 本地引擎 300ms 内出结果，但库大时放宽，仍远小于"loading>1s"红线 */
const TIMEOUT_DIAGNOSE = 8000;

/** Tauri invoke 句柄（运行时由 @tauri-apps/api 提供；dev/浏览器环境为 undefined） */
function getInvoke(): ((cmd: string, args?: unknown) => Promise<unknown>) | undefined {
  const w = window as unknown as { __TAURI_INTERNALS__?: { invoke: (c: string, a?: unknown) => Promise<unknown> } };
  return w.__TAURI_INTERNALS__?.invoke;
}

let seq = 0;
function nextReqId(): string {
  seq += 1;
  return `r-${String(seq).padStart(4, "0")}`;
}

/** 带超时的单次调用；失败/超时一律 resolve(null)，静默不抛 */
export async function call<T>(cmd: string, payload: Record<string, unknown> = {}, timeout = DEFAULT_TIMEOUT): Promise<T | null> {
  const invoke = getInvoke();
  if (!invoke) return null; // 浏览器/预览环境：静默
  const reqId = nextReqId();
  try {
    const raw = (await Promise.race([
      invoke("handle_core_cmd", { reqId, cmd, payload }),
      new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), timeout)),
    ])) as { ok?: boolean; data?: T } | null;
    if (raw && raw.ok === true && raw.data !== undefined) return raw.data;
    return null; // ok=false（错误码）同样静默，视图层降级
  } catch {
    return null;
  }
}

/* ============ §2.4 命令表逐条封装（契约：K 冻结，不改名） ============ */

/** F：存档、设置、库版本、授权状态 */
export const getState = () => call<Record<string, unknown>>("get_state");
/** F：5 题答案落 state.json.last_answers（本地缓存） */
export const saveAnswers = (answers: Record<string, unknown>) => call("save_answers", { answers });
/** C：诊断 → Top3 + checked/filtered + why */
export const diagnose = (answers: Record<string, unknown>) =>
  call<{ ideas: unknown[]; checked: number; filtered: number }>("diagnose", { answers }, TIMEOUT_DIAGNOSE);
/** C+D：完整详情对象（F05 四张内容卡 + 派生字段） */
export const getIdea = (id: string) => call<Record<string, unknown>>("get_idea", { id }, TIMEOUT_DIAGNOSE);
/** E：导出一页 PDF → 文件名、字节数、页数 */
export const exportPlan = (id: string, path: string) =>
  call<{ file_name: string; bytes: number; pages: number }>("export_plan", { id, path });
/** E：成本表 CSV → 文件名 */
export const exportCsv = (id: string, path: string) => call<{ file_name: string }>("export_csv", { id, path });
/** F：保存点子（同 id 去重） */
export const saveIdea = (id: string) => call("save_idea", { id });
/** F：已存列表（saved_at 倒序） */
export const listSaved = () => call<{ items: unknown[] }>("list_saved");
/** F：清空已存（视图层先二次确认） */
export const clearSaved = () => call("clear_saved");
/** F：两两对比 → 三项字段 */
export const compareIdeas = (ids: string[]) => call<Record<string, unknown>>("compare_ideas", { ids });
/** F：读 6 项设置 */
export const getSettings = () => call<Record<string, unknown>>("get_settings");
/** F：写 6 项设置 → 当前设置 */
export const setSettings = (patch: Record<string, unknown>) => call<Record<string, unknown>>("set_settings", { patch });
/** F+A：查库 manifest → 新版本号（失败静默） */
export const checkLibrary = () => call<Record<string, unknown>>("check_library");
/** F+A：应用 delta → 新版本号（失败静默） */
export const applyDelta = (delta: Record<string, unknown>) => call<Record<string, unknown>>("apply_delta", delta);
/** G：激活（码 + 设备指纹由 G 端处理） */
export const activate = (code: string) => call<Record<string, unknown>>("activate", { code });
/** G：授权状态 → 席位数、凭证状态 */
export const licenseStatus = () => call<Record<string, unknown>>("license_status");
/** G：释放本机席位 */
export const releaseSeat = () => call("release_seat");
/** F（默认关）：匿名崩溃记录 */
export const logCrash = (code: string, version: string) => call("log_crash", { code, version });

/**
 * A-05 附属（非 §2.4 sidecar cmd，走 A 的 Tauri 命令层）：
 * 导出完成后打开所在文件夹。A 的 open-folder 命令就绪前静默失败。
 */
export async function openExportFolder(path: string): Promise<void> {
  const invoke = getInvoke();
  if (!invoke) return;
  try {
    await invoke("open_export_folder", { path });
  } catch {
    /* 静默 */
  }
}
