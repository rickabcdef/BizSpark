# 商店技术材料（A-13，A 出技术侧，H 汇总进 qa/store-assets/）

## 应用标识

- ProductName：BizSpark；Identifier：com.bizspark.desktop；版本：1.0.0

## 权限与隐私（供隐私政策与审核说明）

- 应用完全本地运行；联网仅一处：月度增量更新拉取静态托管 manifest/delta（HTTPS GET，3s 超时，失败静默）
- 不监听任何端口、不上传任何用户数据、无遥测
- 采集机器指纹（SHA-256 单向散列，不含 IP/MAC/原始机器 ID），仅用于授权绑定
- 本地文件写入范围：应用数据目录（baseline/delta/存档/设置）

## 打包信息

- Windows：MSIX（Store）+ NSIS/MSI（分销）；包体 ≤80MB 红线（pack.sh 自动校验）
- sidecar：PyInstaller 单文件 bizspark-core，随包分发，stdio JSONL 与壳通信
- 签名：SHA256 + 时间戳（sign.sh，证书仅存在于发布机）

## 9 页功能清单（供商品页文案）

Welcome → Quiz（5 题）→ Results → Detail → Export → Saved → Activate → Library → Settings

## 提交前检查

- [ ] 两版（en/cn）9 张截图与 UI 稿一致（B 重出，H 汇总）
- [ ] 隐私政策文件就位（H）
- [ ] 审核无补件（H 最终把关，A 提供技术说明）
