import asyncio

from astrbot.api.event import filter
from astrbot.api.star import Context, Star, StarTools
from astrbot.core import AstrBotConfig
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .data import KeywordReplyDB


class WbankPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.conf = config
        self.data_dir = StarTools.get_data_dir("astrbot_plugin_wbank")
        self.word_bank_file = self.data_dir / "default_word_bank.json"
        self.db = KeywordReplyDB(self.word_bank_file)


    @filter.command("添加词条")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def add_entry(self, event: AstrMessageEvent):
        """添加词条 示例：添加词条 关键词 内容"""
        args = event.message_str.removeprefix("添加词条").strip().split(" ", 1)
        if len(args) != 2:
            await self.send(event, "格式错误，应为：添加词条 关键词 内容")
            return
        keyword, content = args
        if len(self.db.list_entries(args[0])) >= self.conf["words_limit"]:
            await self.send(event, f"关键词【{keyword}】的词条数量已达上限")
            return
        self.db.add_entry(keyword, content)
        self.db.enable_in_group(keyword, event.get_group_id())
        await self.send(event, f"已添加：{keyword} -> {content}")

    @filter.command("删除词条")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def delete_entry(self, event: AstrMessageEvent):
        """删除词条 示例：删除词条 关键词 序号"""
        args = event.message_str.removeprefix("删除词条").strip().split()
        if len(args) != 2 or not args[1].isdigit():
            await self.send(event, "格式错误，应为：删除词条 关键词 序号")
            return
        keyword, idx = args[0], int(args[1])
        success = self.db.remove_entry_by_index(keyword, idx)
        if success:
            await self.send(event, f"已删除关键词【{keyword}】的第{idx}条词条")
        else:
            await self.send(event, "删除失败，关键词或索引无效")

    @filter.command("删除关键词")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def delete_keyword(self, event: AstrMessageEvent, keyword: str):
        """删除关键词 关键词1 关键词2"""
        keywords = event.message_str.removeprefix("删除关键词").strip().split(" ")
        reply = ""
        for keyword in keywords:
            if keyword not in self.db.data:
                reply += f"关键词【{keyword}】不存在"
                continue
            self.db.delete_keyword(keyword)
            reply += f"已删除关键词：{keyword}"
        await self.send(event, reply.strip())

    @filter.command("设置别名")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def set_alias(self, event: AstrMessageEvent):
        """设置别名 示例：设置别名 关键词 别名1 别名2"""
        args = event.message_str.removeprefix("设置别名").strip().split(" ")
        if len(args) < 2:
            await self.send(event, "格式错误，应为：设置别名 关键词 别名1 别名2")
            return
        keyword, aliases = args[0], args[1:]
        if keyword not in self.db.get_all_keywords():
            await self.send(event, f"关键词【{keyword}】不存在")
            return
        self.db.set_alias(keyword, aliases)
        await self.send(event, f"已设置关键词【{keyword}】的别名：{aliases}")

    @filter.command("启用关键词")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def enable_keyword(self, event: AstrMessageEvent):
        """启用关键词 关键词 群1 群2"""
        args = event.message_str.removeprefix("启用关键词").strip().split(" ")
        if len(args) < 2:
            await self.send(event, "格式错误，应为：启用别名 关键词 群1 群2")
            return
        keyword, groups_id = args[0], args[1:]
        if keyword not in self.db.get_all_keywords():
            await self.send(event, f"关键词【{keyword}】不存在")
            return
        if not groups_id:
            groups_id = [event.get_group_id()]
        reply = ""
        for group_id in groups_id:
            self.db.enable_in_group(keyword, str(group_id))
            reply += f"群({group_id})已启用关键词：\n{keyword}\n"
        await self.send(event, reply.strip())

    @filter.command("禁用关键词")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def disable_keyword(self, event: AstrMessageEvent, keyword: str):
        """禁用关键词 群1 群2"""
        args = event.message_str.removeprefix("禁用关键词").strip().split(" ")
        if len(args) < 2:
            await self.send(event, "格式错误，应为：禁用关键词 关键词 群1 群2")
            return
        keyword, groups_id = args[0], args[1:]
        if keyword not in self.db.get_all_keywords():
            await self.send(event, f"关键词【{keyword}】不存在")
            return
        if not groups_id:
            groups_id = [event.get_group_id()]
        reply = ""
        for group_id in groups_id:
            self.db.disable_in_group(keyword, str(group_id))
            reply += f"群({group_id})已禁用关键词：{keyword}\n"
        await self.send(event, reply.strip())

    @filter.command("查看词条")
    async def list_entries(self, event: AstrMessageEvent, keyword: str):
        """查看某个关键词的所有词条"""
        info = self.db.get_keyword_info(keyword)
        if not info:
            await self.send(event, "未找到该关键词")
            return
        entries = info.get("entries", [])
        aliases = ", ".join(info.get("alias", []))
        groups = ", ".join(info.get("enabled_groups", []))
        msg = f"关键词【{keyword}】词条：\n" + "\n".join(
            [f"{i + 1}. {e}" for i, e in enumerate(entries)]
        )
        if aliases:
            msg += f"\n别名：{aliases}"
        msg += f"\n启用群：{groups or '无'}"
        await self.send(event, msg)

    @filter.command("查看所有关键词", alias={"查看所有词条"})
    async def list_all_keywords(self, event: AstrMessageEvent):
        """查看全部关键词列表"""
        keywords = self.db.get_all_keys()
        if not keywords:
            await self.send(event, "暂无关键词")
            return
        await self.send(event, "📚 所有关键词：\n" + "、".join(keywords))

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def handle_message(self, event: AstrMessageEvent):
        """监听群消息自动触发关键词回复"""
        if self.conf["need_prefix"] and not event.is_at_or_wake_command:
            return
        if reply := self.db.get_reply(
            keyword=event.message_str.strip(), group_id=event.get_group_id()
        ):
            await self.send(event, reply)

    async def send(self, event: AstrMessageEvent, message: str):
        """发送消息"""
        if isinstance(event, AiocqhttpMessageEvent):
            message_id = (
                await event.bot.send_msg(
                    group_id=int(event.get_group_id()), message=message
                )
            ).get("message_id")
            event.stop_event()
            if self.conf["recall_time"] > 0:
                await asyncio.sleep(self.conf["recall_time"])
                await event.bot.delete_msg(message_id=message_id)

        else:
            await event.send(event.plain_result(message))
