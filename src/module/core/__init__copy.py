from typing import Callable, Optional
import asyncio

from message import MessageKind, Message
from module.interface import BasicModule
from framework.log import LOGGER, MessageLog

from .msg_queue.fifo_queue import FIFOQueue as MessageQueue


class HandleResult:
    def __init__(self, sound_path: str):
        self.sound_path = sound_path


HandleCallback = Callable[[HandleResult], None]


class BasicCore(BasicModule):
    def __init__(self):
        super().__init__()

        # 初始化消息队列
        self.__msg_queue = MessageQueue()

        self.__handle_callback: HandleCallback | None = None
        self.__callback_task: Optional[asyncio.Task] = None


    def load_config(self):
        pass

    def handle_starting(self):
        self._make_thread(self.__handle)

    # 线程循环处理消息队列（需要开启多线程）
    def __handle(self):
        # 设置事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 当 Core 停止后，处理线程也需要停止
        async def process_messages():
            while self._is_ready:
                await asyncio.sleep(0.5)
                if self.__msg_queue.empty():
                    continue

                # 接收消息
                message = self.__msg_queue.pop()
                LOGGER.log(MessageLog.from_message(message))

                # 生成回答
                response = self._sub_module("bot").talk(message.content)
                LOGGER.log(
                    MessageLog(
                        MessageKind.Assistant,
                        response,
                        # 如果是管理员发送的消息 则需要专门发给管理员
                        to_admin=message.kind == MessageKind.Admin,
                    )
                )

                # 生成语音
                speech = self._sub_module("speaker").speak(response)

                # 响应处理结果, 只有对应回调函数非空时, 才进行处理
                if self.__handle_callback is not None:
                    result = HandleResult(sound_path=speech)

                    if self.__callback_task is not None and not self.__callback_task.done():
                        # 如果上一个任务还没完成，等待它完成，设置超时
                        try:
                            await asyncio.wait_for(self.__callback_task, timeout=10.0)
                        except asyncio.TimeoutError:
                            print("Handle callback task timed out.")

                    self.__callback_task = asyncio.create_task(self.callback_wrapper(result))
                    

            # 核心处理完毕之后 清除消息队列
            self.__msg_queue.clear()

        loop.run_until_complete(process_messages())

    async def callback_wrapper(self, result: HandleResult) -> None:
        if self.__handle_callback is not None:
            return self.__handle_callback(result)

    def send(self, text: Message) -> bool:
        # 只有当处理核心运行时 才能向其添加消息
        if not self.is_running:
            return False

        self.__msg_queue.push(text)
        return True

    def set_handle_callback(self, callback: HandleCallback):
        self.__handle_callback = callback
