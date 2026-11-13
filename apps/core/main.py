# -*- coding: utf-8 -*-
"""BizSpark core sidecar 主循环（JSONL，无端口监听）

协议见需求文档 §2.4 / 附录 C / 附录 D：
  请求：{"req_id":"r-0001","cmd":"diagnose","payload":{...}}（一行一个）
  响应：{"req_id":"r-0001","ok":true,"data":{...}} / {"req_id":"r-0001","ok":false,"error":{...}}

本文件是共享入口：C(引擎) / D(库校验) / E(渲染) / F(状态) / G(授权) 的
handler 通过 CMD_HANDLERS 注册，main 只做分发与错误码包装，不写业务逻辑。
"""
import json
import sys

# 错误码（附录 D，仅内部使用，禁止展示给用户）
E_BAD_REQUEST = {"code": "E_BAD_REQUEST", "recoverable": True}


def _not_implemented(payload):
    """占位 handler：各负责人实现后替换注册。"""
    return None, {"code": "E_NOT_IMPLEMENTED", "message": "handler not registered yet", "recoverable": True}


# cmd -> handler。handler 签名：fn(payload: dict) -> (data | None, error | None)
# 注册点（实现者请在本表挂载，勿改 main 循环）：
#   C  diagnose            （F03 本地匹配引擎）
#   C  quiz_next / quiz_reset（F02 问卷）
#   E  assemble_detail     （F05 详情装配）
#   E  export_pdf / export_csv（F06 导出）
#   F  saved_list / saved_save / merge_delta（F07 / F09）
#   F  settings_get / settings_set（F11）
#   G  activate            （F10 授权激活）
CMD_HANDLERS = {
    "ping": lambda payload: ({"pong": True}, None),
}
_missing = [c for c in ["diagnose", "quiz_next", "quiz_reset", "assemble_detail",
                        "export_pdf", "export_csv", "saved_list", "saved_save",
                        "merge_delta", "settings_get", "settings_set", "activate"]
            if c not in CMD_HANDLERS]
for _c in _missing:
    CMD_HANDLERS[_c] = _not_implemented


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
    except Exception as exc:  # 任何 handler 异常都包装为错误码，不让 sidecar 崩溃
        return {"req_id": req_id, "ok": False,
                "error": {"code": "E_INTERNAL", "message": str(exc), "recoverable": False}}
    if error:
        return {"req_id": req_id, "ok": False, "error": error}
    return {"req_id": req_id, "ok": True, "data": data or {}}


def main():
    """stdio JSONL 主循环：启动一次、常驻（§2.2）。不监听任何端口。"""
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        sys.stdout.write(json.dumps(handle(raw_line), ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
