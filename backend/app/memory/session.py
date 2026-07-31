from collections import defaultdict
class ConversationMemory:
    def __init__(self): self._messages:dict[str,list[dict[str,str]]]=defaultdict(list)
    def add(self,session_id:str,role:str,content:str): self._messages[session_id].append({'role':role,'content':content});self._messages[session_id]=self._messages[session_id][-12:]
    def get(self,session_id:str)->list[dict[str,str]]: return self._messages[session_id]
memory=ConversationMemory()
