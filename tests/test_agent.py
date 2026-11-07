import asyncio
import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from releaseproof.store import Store

@unittest.skipUnless(importlib.util.find_spec('uagents'), 'Optional ACP dependencies not installed')
class ACPTests(unittest.TestCase):
    def test_actual_sdk_messages_acknowledge_and_return_evidence(self):
        from releaseproof.agent import build_protocol
        from uagents_core.contrib.protocols.chat import ChatMessage, ChatAcknowledgement, TextContent, EndSessionContent
        class Context:
            def __init__(self): self.sent=[]
            async def send(self,sender,message): self.sent.append((sender,message))
        with tempfile.TemporaryDirectory() as tmp:
            protocol,handler=build_protocol(Store(Path(tmp)/'db.sqlite3'))
            context=Context();message=ChatMessage(timestamp=datetime.now(timezone.utc),msg_id=uuid4(),content=[TextContent(type='text',text='demo hardcoded')])
            asyncio.run(handler(context,'test-sender',message))
            self.assertIsNotNone(protocol)
            self.assertEqual(len(context.sent),2)
            self.assertIsInstance(context.sent[0][1],ChatAcknowledgement)
            self.assertEqual(context.sent[0][1].acknowledged_msg_id,message.msg_id)
            reply=context.sent[1][1]
            self.assertIsInstance(reply,ChatMessage)
            self.assertIn('FAIL — BLOCKED',reply.content[0].text)
            self.assertIsInstance(reply.content[-1],EndSessionContent)
            self.assertTrue(reply.model_dump_json())
            asyncio.run(handler(context,'test-sender',message))
            self.assertEqual(context.sent[3][1].content[0].text,reply.content[0].text)
            with Store(Path(tmp)/'db.sqlite3').connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0],1)
    def test_connect_flag_is_required(self):
        import subprocess, sys
        p=subprocess.run([sys.executable,'-m','releaseproof.agent'],text=True,capture_output=True)
        self.assertEqual(p.returncode,2)
        self.assertIn('No agent started',p.stderr)
