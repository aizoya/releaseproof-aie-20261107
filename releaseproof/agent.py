"""Optional uAgents ACP adapter. Importing this module never starts an agent."""
import argparse
import os
import hashlib
from datetime import datetime, timezone
from uuid import uuid4
from urllib.parse import urlsplit
from .chat import respond
from .store import Store

def build_protocol(store):
    from uagents import Protocol
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement, ChatMessage, EndSessionContent, TextContent, chat_protocol_spec,
    )
    protocol = Protocol(spec=chat_protocol_spec)
    @protocol.on_message(ChatMessage)
    async def handle_message(ctx, sender, msg):
        await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
        # Ignore non-text items. Never fetch remote attachments or URLs from chat.
        text = '\n'.join(item.text for item in msg.content if isinstance(item, TextContent))
        # Scope retry identity to the sender and message; persist no raw sender identifier.
        request_key=hashlib.sha256((sender+'|'+str(msg.msg_id)).encode()).hexdigest()
        response = respond(text, store,request_key=request_key)
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
            content=[TextContent(type='text', text=response), EndSessionContent(type='end-session')],
        ))
    @protocol.on_message(ChatAcknowledgement)
    async def handle_ack(ctx, sender, msg):
        pass
    return protocol, handle_message

def main():
    parser=argparse.ArgumentParser(description='ReleaseProof ACP adapter; externally connects only with --connect')
    parser.add_argument('--connect',action='store_true')
    parser.add_argument('--db',default='.state/agent-evidence.sqlite3')
    args=parser.parse_args()
    if not args.connect: parser.error('No agent started. --connect requires an approved hosting/registration action.')
    seed=os.environ.get('RELEASEPROOF_AGENT_SEED')
    endpoint=os.environ.get('RELEASEPROOF_AGENT_ENDPOINT','')
    parsed=urlsplit(endpoint)
    if not seed or parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error('Configure a private agent seed and a public HTTPS submit endpoint securely before connecting.')
    from uagents import Agent
    agent=Agent(name='AIZOYA ReleaseProof', seed=seed, port=8001, endpoint=[endpoint], publish_agent_details=True)
    protocol,_=build_protocol(Store(args.db))
    agent.include(protocol,publish_manifest=True)
    agent.run()

if __name__=='__main__': main()
