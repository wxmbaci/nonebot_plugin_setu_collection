from nonebot.plugin.on import on_regex,on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageSegment,
    Message
    )
from nonebot.params import CommandArg,Arg

import nonebot
import re
import httpx
import asyncio
import unicodedata
from os.path import dirname

from .utils import customer_api,save

from .utils import MirlKoi,Anosu,Lolicon,is_MirlKoi_tag

Bot_NICKNAME = list(nonebot.get_driver().config.nickname)

Bot_NICKNAME = Bot_NICKNAME[0] if Bot_NICKNAME else "色图bot"

heisi_group = nonebot.get_driver().config.heisi_group
heisi_cd = nonebot.get_driver().config.heisi_cd
cddir = dirname(__file__) + "/cd"
his = on_command("his", aliases={".黑丝", ".丝袜"})

@his.handle()
async def _(bot: Bot, event: MessageEvent):
    
    
    msg = ""
    cmd = event.get_plaintext()
    N = 1

    try:
        N = int(N)
    except ValueError:
        try:
            N = int(unicodedata.numeric(N))
        except (TypeError, ValueError):
            N = 0

    Tag = re.sub(r'^我?要|^来|.*[张份]', '', cmd)
    Tag = Tag [:-2]if (Tag.endswith("黑丝") or Tag.endswith("白丝")) else Tag

    if Tag.startswith("r18"):
        Tag = Tag [3:]
        R18 = 1
    else:
        R18 = 0

    if isinstance(event,GroupMessageEvent):
        gid = str(event.group_id)
        if gid not in heisi_group:
            logger.info(f"群  {event.group_id} 未开通此功能，发送提示信息 ")
            await bot.send(
                event=event,
                message="当前群未开通此功能"
            )
            return
        cdtxt = cddir + "/" + gid + "cd.txt"
        if not os.path.exists(cddir):
            os.mkdir(cddir)
        cd_time = open(cdtxt, "r").read()
        cd_time = datetime.datetime.strptime(cd_time, "%Y-%m-%d %H:%M:%S.%f")
        now = datetime.datetime.now()
        if int(str((now - cd_time).seconds)) <= int(heisi_cd):
            left = int(heisi_cd) - int(str((now - cd_time).seconds))
            await bot.send(
                event=event,
                message="技能CD中，剩%d秒" % left
            )
            return
        if R18:
            await setu.finish("涩涩是禁止事项！！")
        else:
            if not Tag:
                msg,url_list = MirlKoi(N,Tag,R18)
                api = "MirlKoi API"
            else:
                tag = is_MirlKoi_tag(Tag)
                if tag:
                    msg,url_list = MirlKoi(N,tag,R18)
                    api = "MirlKoi API"
                else:
                    msg,url_list = Anosu(N,Tag,R18)
                    api = "Jitsu"
    else:
        api = customer_api.get(str(event.user_id),None)
        if api == "Lolicon API":
            msg,url_list = Lolicon(N,Tag,R18)
        else:
            if R18:
                msg,url_list = Anosu(N,Tag,R18)
                api = "Jitsu"
            else:
                if not Tag:
                    msg,url_list = MirlKoi(N,Tag,R18)
                    api = "MirlKoi API"
                else:
                    tag = is_MirlKoi_tag(Tag)
                    if tag:
                        msg,url_list = MirlKoi(N,tag,R18)
                        api = "MirlKoi API"
                    else:
                        msg,url_list = Anosu(N,Tag,R18)
                        api = "Jitsu"

    msg = msg.replace("Bot_NICKNAME",Bot_NICKNAME)

    msg += f"\n图片取自：{api}\n"

    if len(url_list) >3:
        msg = msg[:-1]
        await setu.send(msg, at_sender = True)

    async with httpx.AsyncClient() as client:
        task_list = []
        for url in url_list:
            task = asyncio.create_task(func(client,url))
            task_list.append(task)
        image_list = await asyncio.gather(*task_list)

    image_list = [image for image in image_list if image]

    if image_list:
        N = len(image_list)
        if N <= 3:
            image = Message()
            for i in range(N):
                image +=  MessageSegment.image(file = image_list[i])
            await setu.finish(Message(msg) + image, at_sender = True)
        else:
            msg_list =[]
            for i in range(N):
                msg_list.append(
                    {
                        "type": "node",
                        "data": {
                            "name": Bot_NICKNAME,
                            "uin": event.self_id,
                            "content": MessageSegment.image(file = image_list[i])
                            }
                        }
                    )
            if isinstance(event,GroupMessageEvent):
                await bot.send_group_forward_msg(group_id = event.group_id, messages = msg_list)
            else:
                await bot.send_private_forward_msg(user_id = event.user_id, messages = msg_list)
    else:
        msg += "获取图片失败。"
        await setu.finish(msg, at_sender = True)

set_api = on_command("设置api", aliases = {"切换api","指定api"}, priority = 50, block = True)

@set_api.got(
    "api",
    prompt = (
        "请选择:\n"
        "1.Jitsu/MirlKoi API\n"
        "2.Lolicon API"
        )
    )
async def _(bot: Bot, event: PrivateMessageEvent, api: Message = Arg()):
    api = str(api)
    user_id = str(event.user_id)
    if api == "1":
        customer_api[user_id] = "Jitsu/MirlKoi API"
        save()
        await set_api.finish("api已切换为Jitsu/MirlKoi API")
    elif api == "2":
        customer_api[user_id] = "Lolicon API"
        save()
        await set_api.finish("api已切换为Lolicon API")
    else:
        await set_api.finish("api设置失败")

