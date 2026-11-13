# -*- coding: utf-8 -*-
"""BizSpark core sidecar 主循环（JSONL，无端口监听）—— C-01

协议见需求文档 §2.4 / 附录 C / 附录 D：
  请求：{"req_id":"r-0001","cmd":"diagnose","payload":{...}}（一行一个）
  响应：{"req_id":"r-0001","ok":true,"data":{...}} / {"req_id":"r-0001","ok":false,"error":{...}}

本文件负责人：C（任务卡 §6.3「你负责的文件」）。main 只做分发、ready 与错误码包装，不写业务逻辑。
- 启动即输出首行 ready（A 的 bridge.rs 会原样转发给前端，B 按 req_id 匹配不受影响）
- §2.4 命令表**全部可路由**：C 实现的 diagnose / get_idea 为真实现，其余按负责人保留注册点
- 兼容别名：保留早前脚手架（A）的占位 cmd 名，避免破坏既有调用方
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import diagnose as _diagnose, get_idea as _get_idea  # noqa: E402

# 错误码（附录 D，仅内部使用，禁止展示给用户）
E_BAD_REQUEST = {"code": "E_BAD_REQUEST", "recoverable": True}
SIDECAR_VERSION = "1.0.0"


def _not_implemented(payload):
    """占位 handler：各负责人实现后替换注册。"""
    return None, {"code": "E_NOT_IMPLEMENTED", "message": "handler not registered yet", "recoverable": True}


# cmd -> handler。handler 签名：fn(payload: dict) -> (data | None, error | None)
CMD_HANDLERS = {
    "ping": lambda payload: ({"pong": True, "version": SIDECAR_VERSION}, None),
    # —— C（F03 匹配引擎 / §3.4 详情装配）——
    "diagnose": _diagnose,
    "get_idea": _get_idea,
}

# §2.4 命令表其余 cmd：保留注册点，等对应负责人实现后挂载（勿删他人名字）
#   E  export_plan / export_csv（F06 导出）
#   F  get_state / save_answers / save_idea / list_saved / clear_saved / compare_ideas
#      get_settings / set_settings / check_library / apply_delta / log_crash
#      （以及 F09 合并、F07 存档等）
#   G  activate / license_status / release_seat（F10 授权）
_NOT_IMPLEMENTED_CMDS = [
    # §2.4 正名
    "get_state", "save_answers", "export_plan", "export_csv",
    "save_idea", "list_saved", "clear_saved", "compare_ideas",
    "get_settings", "set_settings", "check_library", "apply_delta",
    "activate", "license_status", "release_seat", "log_crash",
    # 早期脚手架别名（保留，兼容既有调用方；负责人实现正名后可下线）
    "quiz_next", "quiz_reset", "assemble_detail", "export_pdf",
    "saved_list", "saved_save", "merge_delta", "settings_get", "settings_set",
]
for _c in _NOT_IMPLEMENTED_CMDS:
    CMD_HANDLERS.setdefault(_c, _not_implemented)


def handle(raw_line):
    """处理一行请求，返回一行响应 dict。"""
    try:
        req = json.loads(raw_line)
    except ValueError:
        return {"req_id": None, "ok": False,
                "error": dict(E_BAD_REQUEST, message="invalid JSON line")}
    req_id = req.get("req_id")
    cmd = req.get("cmd")
    payload = req.get("payload") or {}
    if not req_id or not cmd:
        return {"req_id": req_id, "ok": False,
                "error": dict(E_BAD_REQUEST, message="req_id and cmd are required")}
    handler = CMD_HANDLERS.get(cmd)
    if handler is None:
        return {"req_id": req_id, "ok": False,
                "error": {"code": "E_UNKNOWN_CMD", "message": cmd, "recoverable": True}}
    try:
        data, error = handler(payload)
    except Exception as exc:  # 任何 handler 异常都包装为错误码，不让 sidecar 崩溃；不写用户数据到日志
        return {"req_id": req_id, "ok": False,
                "error": {"code": "E_INTERNAL", "message": str(exc), "recoverable": False}}
    if error:
        return {"req_id": req_id, "ok": False, "error": error}
    return {"req_id": req_id, "ok": True, "data": data or {}}


def _ready_line():
    """首行 ready（§2.2 sidecar 就绪握手）：无 req_id，B 的 req_id 匹配会自然忽略。"""
    return json.dumps({"req_id": None, "ok": True,
                       "data": {"event": "ready", "version": SIDECAR_VERSION}},
                      ensure_ascii=False)


def main():
    """stdio JSONL 主循环：首行 ready → 启动一次、常驻（§2.2）。不监听任何端口、零出网。"""
    sys.stdout.write(_ready_line() + "\n")
    sys.stdout.flush()
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        sys.stdout.write(json.dumps(handle(raw_line), ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
