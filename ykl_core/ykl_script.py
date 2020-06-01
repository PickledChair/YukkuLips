"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

class YKLScript:
    def __init__(self, content):
        self.__block_sep = "--"
        self.__name_sep = "＞"
        self.__content = content

    @staticmethod
    def create_from_text(text):
        lines = text.splitlines()
        content = []
        current_block = []
        for line in lines:
            if line[:2] == "--":
                content.append(current_block)
                current_block = []
            elif len(line) > 0:
                s_speech = line.split("＞")
                if len(s_speech) == 2:
                    current_block.append(tuple(s_speech))
                else:
                    return None
            else:
                continue
        content.append(current_block)
        return YKLScript(content)

    @staticmethod
    def create_from_context(ctx):
        content = []
        for block in ctx.get_sceneblocks():
            content.append(
                [(sozai.get_name(), sozai.speech_content)
                 for sozai in block.get_sozais()
                 if len(sozai.speech_content) > 0])
        return YKLScript(content)

    def into_text(self):
        text = ""
        for i, block in enumerate(self.__content):
            for speech in block:
                text += speech[0] + "＞" + speech[1] + "\n"
            if i != len(self.__content)-1:
                text += "--\n"
        return text

    def dist_into_context(self, ctx):
        for block, s_block in zip(ctx.get_sceneblocks(), self.__content):
            # 全てのキャラ素材のセリフを初期化
            for sozai in block.get_sozais():
                sozai.speech_content = ""
            idx = 0
            for s_speech in s_block:
                found = True
                while block.get_sozais()[idx].get_name() != s_speech[0]:
                    idx += 1
                    if idx >= len(block.get_sozais()):
                        found = False
                        break
                if not found:
                    break
                else:
                    block.get_sozais()[idx].speech_content = s_speech[1]
        context_len = len(ctx.get_sceneblocks())
        diff = len(self.__content) - context_len
        # print(len(self.__content), context_len)
        if diff > 0:
            ctx.set_current_sceneblock(context_len-1)
            ctx.add_sceneblock()
            block = ctx.get_current_sceneblock()
            for sozai in block.get_sozais():
                sozai.speech_content = ""
            for _ in range(diff-1):
                ctx.add_sceneblock()
            for i in range(diff):
                ctx.set_current_sceneblock(context_len+i)
                block = ctx.get_current_sceneblock()
                idx = 0
                for s_speech in self.__content[context_len + i]:
                    found = True
                    while block.get_sozais()[idx].get_name() != s_speech[0]:
                        block.get_sozais()[idx].speech_content = ""
                        idx += 1
                        if idx >= len(block.get_sozais()):
                            found = False
                            break
                    if not found:
                        break
                    else:
                        block.get_sozais()[idx].speech_content = s_speech[1]
                        idx += 1
        ctx.unsaved_check()
