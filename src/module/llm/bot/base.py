from abc import ABCMeta, abstractmethod
from typing import List

class BasicBot(metaclass=ABCMeta):
    system_prompt = "你现在是一名主播，请回答观众问题。"

    def __init__(self):
        pass
    

    # 单条消息的调用（只能输入一条 query）
    @abstractmethod
    def _single_call(self, query: str) -> str:
        ...

    ''' 多条消息的调用（可以通过上下文输入）
        输入格式: {
            role: str,
            content: str
        }
    '''
    # @abstractmethod
    # def _multi_call(self, query: List[dict]) -> str:
    #     ...
    
    def talk(self, query: str) -> str:
        return self._single_call(query)
    
    
    def check(self) -> bool:
        """如果调用后不会报错且能够正常返回，则检验正常

        Returns:
            bool: 是否正常
        """
        try:
            response = self._single_call("hello")
            return response != None
        except:
            return False