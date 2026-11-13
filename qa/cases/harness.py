"""harness.py — H-01/H-02 公共测试脚手架（负责人：H）

所有 T 用例都通过这里与**真实 sidecar**（apps/core/main.py）对话，不 mock 业务逻辑：
  - 每个用例独立 BIZSPARK_APP_DATA 临时目录（互不污染、可并行）
  - JSONL 协议：首行 ready → 按 req_id 收发
  - PDF 文本提取：reportlab 默认 ASCII85+Flate，无 pdftotext 也能逐字校验

约定：本文件不 import 业务模块（除了只读的 fixture 数据），保证"QA 不改业务代码"。
"""

from __future__ import annotations

import base64
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "apps" / "core"
MAIN = CORE / "main.py"
DATA = CORE / "data"
PDF_PY = "python"

READY_TIMEOUT = 20.0


# --------------------------------------------------------------------------- #
# 侧车进程
# --------------------------------------------------------------------------- #
class Sidecar:
    """一条 sidecar 进程 = 一个"安装了软件的用户电脑"。"""

    def __init__(self, app_data: str | None = None, env: dict | None = None,
                 keep: bool = False, script: str | None = None):
        self.app_data = app_data or tempfile.mkdtemp(prefix="bz_qa_")
        self.script = script or str(MAIN)
        self._own_dir = app_data is None
        self.keep = keep
        self.proc: subprocess.Popen | None = None
        self.ready: dict | None = None
        self.stderr_path = os.path.join(self.app_data, "_sidecar.stderr")
        self._q: queue.Queue = queue.Queue()
        self._seq = 0
        self._env = dict(os.environ, BIZSPARK_APP_DATA=self.app_data,
                         PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        if env:
            self._env.update({k: str(v) for k, v in env.items()})

    # -- 生命周期 -------------------------------------------------------- #
    def start(self) -> "Sidecar":
        self._stderr_fh = open(self.stderr_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(
            [sys.executable, self.script],
            cwd=str(REPO), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self._stderr_fh,
            text=True, encoding="utf-8", bufsize=1, env=self._env,
        )
        threading.Thread(target=self._pump, daemon=True).start()
        first = self._next_line(READY_TIMEOUT)
        if not first:
            raise RuntimeError("sidecar 未在 %.0fs 内输出 ready：%s" % (READY_TIMEOUT, self.tail_stderr()))
        msg = json.loads(first)
        self.ready = msg.get("data") or {}
        if self.ready.get("event") != "ready":
            raise RuntimeError("首行不是 ready 事件：%s" % first[:200])
        return self

    def _pump(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            line = line.strip()
            if line:
                self._q.put(line)

    def _next_line(self, timeout: float) -> str | None:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def call(self, cmd: str, payload: dict | None = None, timeout: float = 60.0) -> dict:
        """发一条请求，返回完整响应行（含 req_id/ok/data|error）。"""
        return self._send({"cmd": cmd, "payload": payload or {}}, timeout)

    def _send(self, req: dict, timeout: float) -> dict:
        assert self.proc and self.proc.stdin
        self._seq += 1
        req_id = "q%d" % self._seq
        req = dict(req, req_id=req_id)
        self.proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._next_line(max(0.05, deadline - time.time()))
            if line is None:
                raise TimeoutError("%s 超时 %.1fs" % (req["cmd"], timeout))
            msg = json.loads(line)
            if msg.get("req_id") == req_id:
                return msg
        raise TimeoutError("%s 超时 %.1fs" % (req["cmd"], timeout))

    def ok(self, cmd: str, payload: dict | None = None, timeout: float = 60.0) -> dict:
        """要求成功，直接返回 data（失败即抛，便于用例断言）。"""
        r = self.call(cmd, payload, timeout)
        if not r.get("ok"):
            raise AssertionError("%s 返回错误：%s" % (cmd, json.dumps(r.get("error"), ensure_ascii=False)))
        return r.get("data") or {}

    def err(self, cmd: str, payload: dict | None = None, timeout: float = 60.0) -> dict:
        """要求失败，返回 error 对象。"""
        r = self.call(cmd, payload, timeout)
        if r.get("ok"):
            raise AssertionError("%s 预期失败但成功了：%s" % (cmd, json.dumps(r.get("data"), ensure_ascii=False)[:200]))
        return r.get("error") or {}

    def raw_line(self, line: str, timeout: float = 20.0) -> dict | None:
        """发原始行（测脏 JSON 不崩）。"""
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            got = self._next_line(max(0.05, deadline - time.time()))
            if got is None:
                return None
            try:
                return json.loads(got)
            except ValueError:
                continue
        return None

    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin and self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        fh = getattr(self, "_stderr_fh", None)
        if fh and not fh.closed:
            fh.close()
        if self.proc and self.proc.stdout and not self.proc.stdout.closed:
            try:
                self.proc.stdout.close()
            except Exception:
                pass

    def cleanup(self) -> None:
        self.stop()
        if self._own_dir and not self.keep:
            shutil.rmtree(self.app_data, ignore_errors=True)

    def __enter__(self) -> "Sidecar":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.cleanup()

    # -- 便捷读取 -------------------------------------------------------- #
    def state(self) -> dict:
        return self.ok("get_state")

    def tail_stderr(self, n: int = 1200) -> str:
        try:
            return Path(self.stderr_path).read_text(encoding="utf-8", errors="replace")[-n:]
        except OSError:
            return ""

    def app_file(self, *parts: str) -> str:
        return os.path.join(self.app_data, *parts)


# --------------------------------------------------------------------------- #
# 只读数据
# --------------------------------------------------------------------------- #
def load_baseline() -> list[dict]:
    raw = json.loads((DATA / "baseline_v1.json").read_text(encoding="utf-8"))
    ideas = raw["ideas"] if isinstance(raw, dict) else raw
    return ideas


def load_fallback() -> list[dict]:
    raw = json.loads((DATA / "fallback_ideas.json").read_text(encoding="utf-8"))
    return raw["ideas"] if isinstance(raw, dict) else raw


def locales(lang: str) -> dict:
    return json.loads((REPO / "apps" / "web" / "src" / "locales" / ("%s.json" % lang)).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# PDF 校验（零外部依赖）
# --------------------------------------------------------------------------- #
def pdf_raw(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def pdf_pages(path: str) -> int:
    """/Type /Page 计数（排除 /Pages）。"""
    raw = pdf_raw(path)
    return len(re.findall(rb"/Type\s*/Page[^s]", raw))


def _decode_stream(body: bytes) -> str | None:
    """PDF 流：可能是 Flate / ASCII85+Flate / 明文，逐个试。"""
    body = body.strip(b"\r\n")
    if not body:
        return None
    candidates = []
    # ASCII85（reportlab 默认）：去掉 <~ ~> 后按 ignorechars 解码
    try:
        stripped = body.replace(b"<~", b"").replace(b"~>", b"")
        candidates.append(base64.a85decode(stripped, ignorechars=b" \t\n\r\v\f"))
    except Exception:
        pass
    candidates.append(body)  # 明文流
    for blob in candidates:
        try:
            return zlib.decompress(blob).decode("latin-1", "ignore")
        except zlib.error:
            pass
        txt = blob.decode("latin-1", "ignore")
        if "Tj" in txt or "TJ" in txt or "BT" in txt:
            return txt
    return None


def _streams(raw: bytes) -> list[bytes]:
    """按 `stream\\r?\\n` … `endstream` 切块（注意不能直接 split(b"stream")，
    否则会命中 endstream 里的 stream）。"""
    out = []
    for m in re.finditer(rb"stream\r?\n", raw):
        start = m.end()
        end = raw.find(b"endstream", start)
        if end > start:
            out.append(raw[start:end])
    return out


def pdf_text(path: str) -> str:
    """把可见文本拼出来（reportlab 内容流 → 括号串）。"""
    raw = pdf_raw(path)
    chunks: list[str] = []
    for body in _streams(raw):
        txt = _decode_stream(body)
        if txt:
            chunks.append(txt)
    joined = "\n".join(chunks)
    # (…) Tj 与 [(…) …] TJ 两种写法
    out = []
    for m in re.finditer(r"\((?:\\.|[^\\()])*\)", joined):
        s = m.group(0)[1:-1]
        s = (s.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
             .replace(r"\n", "\n").replace(r"\r", ""))
        out.append(s)
    return "\n".join(out)


def pdf_has_url(path: str) -> bool:
    raw = pdf_raw(path).lower()
    text = pdf_text(path).lower()
    return (b"/uri" in raw) or ("http://" in text) or ("https://" in text) or ("www." in text)


def pdf_fonts(path: str) -> set[str]:
    return {m.decode("latin-1") for m in re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-]+)", pdf_raw(path))}


# --------------------------------------------------------------------------- #
# 杂项
# --------------------------------------------------------------------------- #
def sh(cmd: list[str] | str, cwd: str | Path | None = None, timeout: int = 300,
       env: dict | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd or REPO), shell=isinstance(cmd, str),
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def default_answers(**over) -> dict:
    base = {"country": "US", "capital": "<500", "hours": "<10",
            "assets": ["laptop"], "risk": "no_impact"}
    base.update(over)
    return base


def demo_codes() -> list[str]:
    """G 的演示码（G-02 签发）。缺失时返回空列表，相关用例 skip 而不是假通过。"""
    path = os.path.join(os.environ.get("APPDATA", ""), "BizSpark-issuer", "codes-2026-11-dev.txt")
    try:
        return [l.strip() for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return []


def fake_png(path: str, size: tuple[int, int] = (8, 8)) -> str:
    """生成最小 PNG（用于占位图标/尺寸类断言，不走外部库）。"""
    import struct
    w, h = size

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes([242, 101, 58] * w) for _ in range(h))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    Path(path).write_bytes(png)
    return path


def png_size(path: str) -> tuple[int, int]:
    import struct
    raw = Path(path).read_bytes()
    w, h = struct.unpack(">II", raw[16:24])
    return w, h
