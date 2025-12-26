import json
from pathlib import Path
from random import choice


class KeywordReplyDB:
    def __init__(self, path: Path):
        """初始化关键词数据库并从指定路径加载数据"""
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        """加载 JSON 文件内容"""
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save(self):
        """将当前数据保存到文件"""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _resolve_keyword(self, keyword: str) -> str | None:
        """根据关键词或其别名返回实际关键词"""
        if keyword in self.data:
            return keyword
        for key, val in self.data.items():
            if "alias" in val and keyword in val["alias"]:
                return key
        return None

    def add_keyword(self, keyword: str):
        """添加新关键词（若不存在）"""
        if keyword not in self.data:
            self.data[keyword] = {"entries": [], "enabled_groups": [], "alias": []}

    def add_entry(self, keyword: str, content: str):
        """为关键词添加一个词条"""
        self.add_keyword(keyword)
        if content not in self.data[keyword]["entries"]:
            self.data[keyword]["entries"].append(content)
            self.save()

    def remove_entry(self, keyword: str, content: str):
        """移除关键词下的指定词条内容"""
        if keyword in self.data and content in self.data[keyword]["entries"]:
            self.data[keyword]["entries"].remove(content)
            self.save()

    def remove_entry_by_index(self, keyword: str, index: int) -> bool:
        """根据索引删除关键词下的词条，成功返回 True"""
        resolved = self._resolve_keyword(keyword)
        if resolved is not None:
            entries = self.data[resolved]["entries"]
            if 0 <= index < len(entries):
                del entries[index]
                self.save()
                return True
        return False

    def list_entries(self, keyword: str) -> list[str]:
        """列出关键词下的所有词条"""
        resolved = self._resolve_keyword(keyword)
        if resolved is not None:
            return self.data[resolved]["entries"]
        return []

    def set_alias(self, keyword: str, aliases: list[str]):
        """设置关键词的别名列表"""
        self.add_keyword(keyword)
        self.data[keyword]["alias"] = aliases
        self.save()

    def add_alias(self, keyword: str, alias: str):
        """为关键词添加一个别名"""
        self.add_keyword(keyword)
        if alias not in self.data[keyword]["alias"]:
            self.data[keyword]["alias"].append(alias)
            self.save()

    def enable_in_group(self, keyword: str, group_id: str):
        """启用关键词在指定群聊中生效"""
        self.add_keyword(keyword)
        if group_id not in self.data[keyword]["enabled_groups"]:
            self.data[keyword]["enabled_groups"].append(group_id)
            self.save()

    def disable_in_group(self, keyword: str, group_id: str):
        """禁用关键词在指定群聊中生效"""
        if keyword in self.data and group_id in self.data[keyword]["enabled_groups"]:
            self.data[keyword]["enabled_groups"].remove(group_id)
            self.save()

    def is_enabled(self, keyword: str, group_id: str) -> bool:
        """判断关键词在指定群聊中是否启用"""
        resolved = self._resolve_keyword(keyword)
        return (
            resolved is not None and group_id in self.data[resolved]["enabled_groups"]
        )

    def get_reply(self, keyword: str, group_id: str) -> str | None:
        """获取关键词在指定群聊下的随机回复（若启用）"""
        resolved = self._resolve_keyword(keyword)
        if resolved and group_id in self.data[resolved]["enabled_groups"]:
            entries = self.data[resolved]["entries"]
            return choice(entries) if entries else None
        return None

    def delete_keyword(self, keyword: str):
        """删除整个关键词及其数据"""
        if keyword in self.data:
            del self.data[keyword]
            self.save()

    def get_all_keywords(self) -> list[str]:
        """获取所有关键词（含别名）"""
        all_keys = []
        for key, value in self.data.items():
            all_keys.append(key)
            if "alias" in value and value["alias"]:
                all_keys.extend(value["alias"])
        return all_keys

    def get_all_keys(self):
        """获取所有关键词（不含别名）"""
        return list(self.data.keys())

    def get_keyword_info(self, keyword: str) -> dict | None:
        """获取关键词的完整信息（支持别名解析）"""
        resolved = self._resolve_keyword(keyword)
        if resolved is not None:
            return self.data.get(resolved)
        return None
