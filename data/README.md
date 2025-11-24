# Data 目录说明

此目录用于存储应用运行时的数据文件。

## 文件说明

- `daily_user_usage.json` - 用户每日使用记录文件
  - 存储格式：`{"日期": {"用户ID": 使用次数}}`
  - 自动在首次运行时创建
  - 数据按日期组织，每天自动重置计数

## 注意事项

⚠️ 此目录中的 JSON 文件包含用户使用数据，已在 `.gitignore` 中配置，**不会被提交到 Git 仓库**。

## 数据管理

### 查看当前数据
```bash
cat ./data/daily_user_usage.json
```

### 清空所有数据
```bash
echo '{}' > ./data/daily_user_usage.json
```

### 备份数据
```bash
cp ./data/daily_user_usage.json ./data/daily_user_usage.backup.json
```

---

此目录由应用自动管理，通常不需要手动操作。
