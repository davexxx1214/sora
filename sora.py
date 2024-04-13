import json
import re
import plugins
from bridge.reply import Reply, ReplyType
from bridge.context import ContextType
from channel.chat_message import ChatMessage
from plugins import *
from common.log import logger
import replicate

import os
import uuid
import os
import uuid
from glob import glob
import translators as ts

@plugins.register(
    name="sora",
    desire_priority=2,
    desc="A plugin to call sora API",
    version="0.0.1",
    author="davexxx",
)

class sunoplayer(Plugin):
    def __init__(self):
        super().__init__()
        try:
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                # 使用父类的方法来加载配置
                self.config = super().load_config()

                if not self.config:
                    raise Exception("config.json not found")
            
            # 设置事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            # 从配置中提取所需的设置
            os.environ['REPLICATE_API_TOKEN'] = self.config.get("REPLICATE_API_TOKEN","")
            self.dreambooth = self.config.get("dreambooth","RealisticVisionV60B1_v51VAE.safetensors")
            self.sora_prefix = self.config.get("sora_prefix", "时光机")

            # 初始化成功日志
            logger.info("[sora] inited.")
        except Exception as e:
            # 初始化失败日志
            logger.warn(f"sora init failed: {e}")
    def on_handle_context(self, e_context: EventContext):
        context = e_context["context"]
        if context.type not in [ContextType.TEXT, ContextType.SHARING,ContextType.FILE,ContextType.IMAGE]:
            return
        content = context.content

        if e_context['context'].type == ContextType.TEXT:
            if content.startswith(self.sora_prefix):
                # Call new function to handle search operation
                pattern = self.sora_prefix + r"\s(.+)"
                match = re.match(pattern, content)
                if match: ##   匹配上了sora的指令
                    logger.info("calling sora service")
                    prompt = content[len(self.sora_prefix):].strip()
                    sora_prompt = self.translate_to_english(prompt)
                    logger.info(f"sora prompt = : {sora_prompt}")
                    try:
                        self.call_sora_service(sora_prompt, e_context)
                    except Exception as e:
                        logger.error("create sora error: {}".format(e))
                        rt = ReplyType.TEXT
                        rc = "服务暂不可用"
                        reply = Reply(rt, rc)
                        e_context["reply"] = reply
                        e_context.action = EventAction.BREAK_PASS
                else:
                    tip = f"💡欢迎使用MagicTime，指令格式为:\n\n{self.sora_prefix}+空格+提示词\n例如:\n{self.sora_prefix} Bean sprouts grow and mature from seeds"
                    reply = Reply(type=ReplyType.TEXT, content= tip)
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS    

    def call_sora_service(self, prompt, e_context):
        input =  {
            "prompt": {prompt},
            "n_prompt":  "worst quality, low quality, nsfw, logo",
            "width":  512,
            "height":  512,
            "seed":  "-1",
            "dreambooth":  "RealisticVisionV60B1_v51VAE.safetensors"
            }

        output = replicate.run(
            "camenduru/magictime:91e4bb80b45832b5bafdbc10d94fd1d364d0d6ad80f5b1498fcb25d217cb3a9c",
            input=input
        )

        # tip = '您的作曲之旅已经启航，让我们的音乐小精灵带上您的歌词飞向创意的宇宙！请耐心等待2~5分钟，您的个人音乐风暴就会随着节拍轻轻降落。准备好一起摇摆吧！🚀'
        # self.send_reply(tip, e_context)
        if "mp4" in output:
            rt = ReplyType.VIDEO_URL
            rc = output
            reply = Reply(rt, rc)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

        else:
            rt = ReplyType.TEXT
            rc = "生成失败"
            reply = Reply(rt, rc)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def translate_to_english(self, text):    
        return ts.translate_text(text, translator='alibaba')
